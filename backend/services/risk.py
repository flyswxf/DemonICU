from typing import Dict, Any, Optional
from .. import constants as C


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


def read_model_probability() -> Optional[float]:
    """Read cardiogenic_shock probability from MODEL_OUT_JSON if available.

    Expected structure examples:
    - { "cardiogenic_shock": 0.37 }
    - { "probabilities": { "cardiogenic_shock": 0.37 } }
    - { "risk": { "cardiogenic_shock": 0.37 } }

    Returns None if file missing or key not found.
    """
    try:
        if not C.MODEL_OUT_JSON.exists():
            return None
        import json
        with open(C.MODEL_OUT_JSON, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            # direct key
            val = data.get("cardiogenic_shock")
            if isinstance(val, (int, float)):
                return max(0.0, min(1.0, float(val)))
            # nested mappings
            # 这后面的应该不需要
            for k in ("probabilities", "risk", "scores"):
                m = data.get(k)
                if isinstance(m, dict):
                    v = m.get("cardiogenic_shock")
                    if isinstance(v, (int, float)):
                        return max(0.0, min(1.0, float(v)))
    except Exception:
        return None
    return None


# 从原 similar 模块迁移：根据补充文本调整概率的辅助函数
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