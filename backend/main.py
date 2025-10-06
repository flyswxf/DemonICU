from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import uuid
import random
from typing import List, Dict, Any, Optional
import subprocess
import sys
from pathlib import Path
import os

app = FastAPI(title="GraphCare Demo Backend", version="1.1.0")

# CORS: allow all origins for demo purposes
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory session store
SESSIONS: Dict[str, Dict[str, Any]] = {}
ROOT_DIR = Path(__file__).resolve().parent.parent
UPLOAD_DIR = ROOT_DIR / "uploads"
MODEL_OUT_JSON = ROOT_DIR / "ehr_baselines" / "SparseTest" / "result" / "inference_result.json"
MODEL_OUT_WITH_NAMES_JSON = ROOT_DIR / "ehr_baselines" / "SparseTest" / "result" / "inference_result_with_names.json"


class MeasureItem(BaseModel):
    measure: str
    reason: Optional[str] = None


class SimilarCaseItem(BaseModel):
    measure: str
    frequency: float  # 0.0 - 1.0


class InferResponse(BaseModel):
    session_id: str
    probability: float
    recommended: List[MeasureItem]
    similar_cases: List[SimilarCaseItem]


class AugmentRequest(BaseModel):
    session_id: str
    text: str


def _ensure_dirs():
    try:
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass


def _save_patient(session_id: str, raw_json: bytes) -> Path:
    _ensure_dirs()
    path = UPLOAD_DIR / f"{session_id}.json"
    with open(path, "wb") as f:
        f.write(raw_json)
    return path


def _run_external_model(patient_id: str) -> None:
    cmd = [
        sys.executable,
        "-u",
        str(ROOT_DIR / "ehr_baselines" / "SparseTest" / "runSparseModel.py"),
        "--dataset",
        "mimic3",
        "--task",
        "drugrec",
        "--infer",
        "--weights_path",
        str(ROOT_DIR / "data" / "weights" / "saved_weights_mimic3_drugrec_sparse.pkl"),
        "--out",
        str(MODEL_OUT_JSON),
        "--patient_id",
        str(patient_id),
    ]
    subprocess.run(cmd, cwd=str(ROOT_DIR), check=True)

    # 先尝试带参数的转换调用（你会在脚本中支持 --input/--output）；不支持参数时降级为无参调用（脚本内部使用默认路径）
    try:
        convert_cmd = [
            sys.executable,
            str(ROOT_DIR / "ehr_baselines" / "SparseTest" / "utils" / "convert_indices_to_code.py"),
            "--input",
            str(MODEL_OUT_JSON),
            "--output",
            str(MODEL_OUT_WITH_NAMES_JSON),
        ]
        subprocess.run(convert_cmd, cwd=str(ROOT_DIR), check=True)
    except subprocess.CalledProcessError:
        fallback_cmd = [
            sys.executable,
            str(ROOT_DIR / "ehr_baselines" / "SparseTest" / "utils" / "convert_indices_to_code.py"),
        ]
        subprocess.run(fallback_cmd, cwd=str(ROOT_DIR), check=True)


def _parse_model_recommendations(max_items: int = 5) -> List[str]:
    if not MODEL_OUT_WITH_NAMES_JSON.exists():
        raise RuntimeError("模型输出未生成")
    with open(MODEL_OUT_WITH_NAMES_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)
    names = []
    if isinstance(data, dict):
        if "topk_names" in data and isinstance(data["topk_names"], list):
            names = data["topk_names"]
        elif "recommendations" in data and isinstance(data["recommendations"], list):
            for it in data["recommendations"]:
                n = it.get("drug_name") or it.get("name")
                if n:
                    names.append(n)
    names = names[:max_items] if max_items and isinstance(names, list) else names
    return [str(n) for n in names]


def _safe_get(d: Dict[str, Any], *keys, default=None):
    cur = d
    for k in keys:
        if isinstance(cur, dict) and k in cur:
            cur = cur[k]
        else:
            return default
    return cur


def compute_base_probability(patient: Dict[str, Any]) -> float:
    # Heuristic demo scoring (not a medical device)
    score = 0.25
    vitals = patient.get("vitals", {}) or {}
    labs = patient.get("labs", {}) or {}
    history = patient.get("history", {}) or {}

    map_val = vitals.get("MAP")  # mean arterial pressure
    ci = vitals.get("CI")  # cardiac index
    pawp = vitals.get("PAWP")  # pulmonary artery wedge pressure
    hr = vitals.get("HR")
    lact = labs.get("lactate")
    ef = labs.get("EF")  # ejection fraction
    urine = labs.get("urine_output_6h") or labs.get("urine_output_24h")

    if map_val is not None and map_val < 65:
        score += 0.18
    if ci is not None and ci < 2.2:
        score += 0.17
    if pawp is not None and pawp > 18:
        score += 0.10
    if hr is not None and hr > 110:
        score += 0.05
    if lact is not None and lact >= 2:
        score += 0.12
    if ef is not None and ef < 35:
        score += 0.12
    if urine is not None:
        try:
            if urine < 0.5:  # ml/kg/h rough proxy
                score += 0.08
        except Exception:
            pass

    # history markers
    if (history.get("AMI_recent") or history.get("STEMI") or history.get("MI")):
        score += 0.08

    return max(0.01, min(0.98, score))


def analyze_text_adjustment(text: str) -> float:
    if not text:
        return 0.0
    t = text.lower()
    inc_keywords = [
        "低血压", "血压下降", "心率过快", "尿量减少", "少尿", "乳酸", "皮肤冰冷", "四肢冰冷", "皮肤湿冷",
        "st段抬高", "心肌梗死", "mi", "左室功能不全", "ef降低", "灌注不足", "意识模糊",
    ]
    dec_keywords = [
        "好转", "稳定", "无胸痛", "症状缓解", "灌注改善", "意识清醒", "血压稳定",
    ]
    delta = 0.0
    for kw in inc_keywords:
        if kw in t:
            delta += 0.04
    for kw in dec_keywords:
        if kw in t:
            delta -= 0.03
    return max(-0.25, min(0.25, delta))


def make_recommendations_from_model(patient_id: str) -> List[MeasureItem]:
    _run_external_model(patient_id)
    names = _parse_model_recommendations(max_items=5)
    return [MeasureItem(measure=n, reason="—") for n in names]


def _extract_patient_id(payload: Dict[str, Any]) -> str:
    pid = payload.get("patient_id")
    if pid is None:
        raise HTTPException(status_code=400, detail="缺少必填字段 patient_id")
    return str(pid)


def make_similar_cases(prob: float, seed: str) -> List[SimilarCaseItem]:
    rng = random.Random(seed)
    base = prob
    items = [
        ("去甲肾上腺素滴定", max(0.15, min(0.95, base + rng.uniform(-0.1, 0.1)))),
        ("正性肌力（多巴酚丁胺/米力农）", max(0.05, min(0.85, base - 0.1 + rng.uniform(-0.1, 0.1)))),
        ("IABP 评估/使用", max(0.05, min(0.7, base - 0.2 + rng.uniform(-0.1, 0.1)))),
        ("VA-ECMO 转诊/启动", max(0.02, min(0.5, base - 0.3 + rng.uniform(-0.1, 0.1)))),
    ]
    # Normalize to look like proportions used among相似病例
    total = sum(x[1] for x in items)
    if total <= 0:
        total = 1.0
    items = [(name, val / total) for name, val in items]
    return [SimilarCaseItem(measure=name, frequency=round(val, 3)) for name, val in items]


@app.post("/api/infer/upload", response_model=InferResponse)
async def infer_from_upload(file: UploadFile = File(...)):
    if file.content_type not in ("application/json", "text/json", "application/octet-stream"):
        raise HTTPException(status_code=400, detail="请上传JSON文件（application/json）")
    raw = await file.read()
    try:
        payload = json.loads(raw.decode("utf-8"))
    except Exception:
        raise HTTPException(status_code=400, detail="无法解析JSON内容")

    session_id = str(uuid.uuid4())
    base_prob = compute_base_probability(payload)
    patient_id = _extract_patient_id(payload)

    prob = base_prob
    try:
        dataset_path = _save_patient(session_id, raw)
        recs = make_recommendations_from_model(patient_id)
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"模型运行失败: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"模型处理失败: {e}")
    sims = make_similar_cases(prob, seed=session_id)

    SESSIONS[session_id] = {"patient": payload, "notes": [], "prob": prob, "dataset_path": str(dataset_path), "patient_id": patient_id}

    return InferResponse(
        session_id=session_id,
        probability=round(prob, 3),
        recommended=recs,
        similar_cases=sims,
    )


@app.post("/api/infer/augment", response_model=InferResponse)
async def augment_with_text(body: AugmentRequest):
    session = SESSIONS.get(body.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="session_id不存在或已过期")
    session["notes"].append(body.text)

    base_prob = compute_base_probability(session["patient"])  # base from patient
    delta = sum(analyze_text_adjustment(t) for t in session["notes"])  # cumulative text impact
    prob = max(0.01, min(0.98, base_prob + delta))
    session["prob"] = prob

    try:
        pid = session.get("patient_id")
        if pid:
            recs = make_recommendations_from_model(str(pid))
        else:
            raise RuntimeError("缺少 patient_id，无法重新运行模型")
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"模型运行失败: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"模型处理失败: {e}")
    sims = make_similar_cases(prob, seed=body.session_id)

    return InferResponse(
        session_id=body.session_id,
        probability=round(prob, 3),
        recommended=recs,
        similar_cases=sims,
    )


@app.get("/api/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000)