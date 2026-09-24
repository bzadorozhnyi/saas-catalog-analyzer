from typing import Literal

from pydantic import BaseModel, ConfigDict

from app.models.category import SoftwareCategory


class ClassifyResponse(BaseModel):
    category: SoftwareCategory
    confidence: float
    reasoning: str


class CatalogItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str
    category: SoftwareCategory


class DuplicatePairResponse(BaseModel):
    name_a: str
    name_b: str
    similarity: float
    verdict: Literal["likely_duplicate", "review_manually"]


class ExplainDuplicateResponse(BaseModel):
    is_duplicate: bool
    confidence: float
    reasoning: str
    overlapping_features: list[str]
