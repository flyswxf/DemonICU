import json
from typing import List
from .. import constants as C
from .model_runner import run_external_model, run_convert_with_fallback


def parse_model_recommendations(max_items: int = 5) -> List[str]:
    if not C.MODEL_OUT_WITH_NAMES_JSON.exists():
        raise RuntimeError("模型输出未生成")
    with open(C.MODEL_OUT_WITH_NAMES_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)
    names: List[str] = []
    if isinstance(data, dict):
        if "topk_names" in data and isinstance(data["topk_names"], list):
            names = data["topk_names"]
        elif "recommendations" in data and isinstance(data["recommendations"], list):
            for it in data["recommendations"]:
                n = it.get("drug_name") or it.get("name")
                if n:
                    names.append(str(n))
    return names[:max_items] if max_items and isinstance(names, list) else names


def recommend_from_model(patient_id: str) -> List[str]:
    run_external_model(patient_id)
    run_convert_with_fallback()
    return parse_model_recommendations(max_items=5)