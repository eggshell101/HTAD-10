from pydantic import BaseModel
from typing import Optional


class Evidence(BaseModel):
    source: str
    title: str
    date: Optional[str] = None
    abstract: Optional[str] = None
    url: Optional[str] = None
    identifier: Optional[str] = None


class RepurposingSignal(BaseModel):
    drug: str
    disease: str
    target: Optional[str] = None

    evidence_score: float = 0.0
    clinical_score: float = 0.0
    quantum_score: float = 0.0

    final_score: float = 0.0

    evidence: list[Evidence] = []