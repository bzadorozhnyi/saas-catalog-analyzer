from pydantic import BaseModel


class ClassifyRequest(BaseModel):
    name: str
    description: str


class CreateCatalogItemRequest(BaseModel):
    name: str
    description: str


class FindDuplicatesRequest(BaseModel):
    subscription_names: list[str]


class ExplainDuplicateRequest(BaseModel):
    name_a: str
    name_b: str
