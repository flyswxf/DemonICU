from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import json
import uuid
import subprocess
from typing import Dict, Any

# Import modularized services and schemas
from backend.schemas import MeasureItem, SimilarCaseItem, InferResponse, AugmentRequest
from backend.services.risk import compute_base_probability
from backend.services.similar import analyze_text_adjustment, make_similar_cases
from backend.services.storage import save_patient, save_feedback_text
from backend.services.recommendation import recommend_from_model, recommend_with_feedback

app = FastAPI(title="GraphCare Demo Backend", version="1.2.0")

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


"""
Schemas moved to backend/schemas.py
"""


"""
File save helpers moved to backend/services/storage.py
"""


"""
Model run & conversion moved to backend/services/model_runner.py and recommendation.py
"""


"""
Recommendation parsing moved to backend/services/recommendation.py
"""


"""
Utility helpers removed (unused in current flow)
"""


"""
Risk scoring moved to backend/services/risk.py
"""


"""
Text adjustment and similar-cases moved to backend/services/similar.py
Recommendation orchestration moved to backend/services/recommendation.py
"""


def _extract_patient_id(payload: Dict[str, Any]) -> str:
    pid = payload.get("patient_id")
    if pid is None:
        raise HTTPException(status_code=400, detail="缺少必填字段 patient_id")
    return str(pid)



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
        dataset_path = save_patient(session_id, raw)
        names = recommend_from_model(patient_id)
        recs = [MeasureItem(measure=n, reason="—") for n in names]
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
    
    # IMPORTANT: First save feedback text to response.txt before any processing
    try:
        save_feedback_text(body.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"保存反馈文本失败: {e}")

    base_prob = compute_base_probability(session["patient"])  # base from patient
    delta = sum(analyze_text_adjustment(t) for t in session["notes"])  # cumulative text impact
    prob = max(0.01, min(0.98, base_prob + delta))
    session["prob"] = prob

    try:
        pid = session.get("patient_id")
        if pid:
            names = recommend_with_feedback(str(pid))
            recs = [MeasureItem(measure=n, reason="—") for n in names]
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