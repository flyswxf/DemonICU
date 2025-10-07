import random
from typing import List, Tuple

from ..schemas import SimilarCaseItem


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


def make_similar_cases(prob: float, seed: str) -> List[SimilarCaseItem]:
    rng = random.Random(seed)
    base = prob
    items: List[Tuple[str, float]] = [
        ("去甲肾上腺素滴定", max(0.15, min(0.95, base + rng.uniform(-0.1, 0.1)))),
        ("正性肌力（多巴酚丁胺/米力农）", max(0.05, min(0.85, base - 0.1 + rng.uniform(-0.1, 0.1)))),
        ("IABP 评估/使用", max(0.05, min(0.7, base - 0.2 + rng.uniform(-0.1, 0.1)))),
        ("VA-ECMO 转诊/启动", max(0.02, min(0.5, base - 0.3 + rng.uniform(-0.1, 0.1)))),
    ]
    total = sum(x[1] for x in items) or 1.0
    items = [(name, val / total) for name, val in items]
    return [SimilarCaseItem(measure=name, frequency=round(val, 3)) for name, val in items]