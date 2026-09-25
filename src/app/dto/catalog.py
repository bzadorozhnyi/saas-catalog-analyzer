from typing import NamedTuple

from pydantic import BaseModel


class SimilarPair(NamedTuple):
    name_a: str
    name_b: str
    similarity: float


class CatalogCreationPayload(BaseModel):
    name: str
    description: str
