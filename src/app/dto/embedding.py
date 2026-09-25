from pydantic import BaseModel


class EmbeddingResult(BaseModel):
    embedding: list[float]
    tokens: int
