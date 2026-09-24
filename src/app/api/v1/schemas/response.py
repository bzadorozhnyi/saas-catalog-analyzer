from pydantic import BaseModel

from app.models.category import SoftwareCategory


class ClassifyResponse(BaseModel):
    category: SoftwareCategory
    confidence: float
    reasoning: str
