from pydantic import BaseModel

from app.enums.software_category_enum import SoftwareCategoryEnum


class ClassifyRequest(BaseModel):
    name: str
    description: str


class CreateCatalogItemRequest(BaseModel):
    name: str
    description: str
    category: SoftwareCategoryEnum


class FindDuplicatesRequest(BaseModel):
    subscription_names: list[str]


class ExplainDuplicateRequest(BaseModel):
    name_a: str
    name_b: str
