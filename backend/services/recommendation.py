import json
from typing import List
from .. import constants as C
from .model_runner import (
    run_external_model,
    run_convert_with_fallback,
    run_keyword_extractor,
    run_cluster_mapper,
)


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
    # 测试模式下：不运行模型，直接从现有inference_result.json开始处理
    if C.TEST_MODE:
        # 若已存在带名字的输出则直接解析，否则尝试运行转换脚本
        # if not C.MODEL_OUT_WITH_NAMES_JSON.exists():
        # try:
        #     run_convert_with_fallback()
        # except Exception:
        #     # 转换失败时返回空列表以避免崩溃
        #     return []
        return parse_model_recommendations(max_items=5)
    # 正常模式：运行模型并转换
    run_external_model(patient_id)
    run_convert_with_fallback()
    return parse_model_recommendations(max_items=5)


def recommend_with_feedback(patient_id: str) -> List[str]:
    """Run feedback pipeline then model and return top names."""
    # 测试模式下：跳过反馈流程与模型运行，仅进行转换和解析
    if C.TEST_MODE:
        if not C.MODEL_OUT_WITH_NAMES_JSON.exists():
            try:
                run_convert_with_fallback()
            except Exception:
                return []
        return parse_model_recommendations(max_items=5)

    # 正常模式：执行反馈预处理 -> 模型 -> 转换
    run_keyword_extractor()
    run_cluster_mapper()
    # Run model with feedback flag
    run_external_model(patient_id, with_feedback=True)
    # Convert indices to names
    run_convert_with_fallback()
    return parse_model_recommendations(max_items=5)