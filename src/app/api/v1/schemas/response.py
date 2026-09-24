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
