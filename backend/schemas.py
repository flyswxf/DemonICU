from typing import List, Optional
from pydantic import BaseModel


class MeasureItem(BaseModel):
    measure: str
    reason: Optional[str] = None


class InferResponse(BaseModel):
    session_id: str
    probability: float
    recommended: List[MeasureItem]


class AugmentRequest(BaseModel):
    session_id: str
    text: str