from pydantic import BaseModel

from app.models.category import SoftwareCategory


class ClassifyRequest(BaseModel):
    name: str
    description: str


class CreateCatalogItemRequest(BaseModel):
    name: str
    description: str
    category: SoftwareCategory
