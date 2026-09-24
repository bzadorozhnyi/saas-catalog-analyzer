from pydantic import BaseModel

from app.models.category import SoftwareCategory


class ClassifyRequest(BaseModel):
    name: str
    description: str


class CreateCatalogItemRequest(BaseModel):
    name: str
    description: str
    category: SoftwareCategory


class FindDuplicatesRequest(BaseModel):
    subscription_names: list[str]
