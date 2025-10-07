from typing import List, Optional
from pydantic import BaseModel


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