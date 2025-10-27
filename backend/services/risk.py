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