import uuid
from typing import Literal

from pydantic import BaseModel, ConfigDict

from app.enums.request_status_enum import RequestStatusEnum
from app.enums.software_category_enum import SoftwareCategoryEnum


class ClassifyResponse(BaseModel):
    category: SoftwareCategoryEnum
    confidence: float
    reasoning: str


class CatalogItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str
    category: SoftwareCategoryEnum


class CreateCatalogItemAcceptedResponse(BaseModel):
    request_id: uuid.UUID


class RequestStatusResponse(BaseModel):
    request_id: uuid.UUID
    status: RequestStatusEnum
    result_item_id: int | None


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
