from pydantic import BaseModel, Field

from app.models.category import SoftwareCategory


class ClassificationResult(BaseModel):
    category: SoftwareCategory
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str


class ExplainDuplicateResult(BaseModel):
    is_duplicate: bool
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str
    overlapping_features: list[str]
