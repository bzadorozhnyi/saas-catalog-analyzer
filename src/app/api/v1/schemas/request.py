import uuid

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
    pair_id: uuid.UUID


class GenerateReportRequest(BaseModel):
    check_id: uuid.UUID
    report_version: str = "v1"
