from pydantic import BaseModel, Field

from app.enums.software_category_enum import SoftwareCategoryEnum


class ClassificationResult(BaseModel):
    category: SoftwareCategoryEnum
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str


class ExplainDuplicateResult(BaseModel):
    is_duplicate: bool
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str
    overlapping_features: list[str]
