from openai import AsyncOpenAI

from app.core.config import settings
from app.dto.embedding import EmbeddingResult


class EmbeddingClient:
    def __init__(self) -> None:
        self._client = AsyncOpenAI(api_key=settings.AI.OPENAI_API_KEY)

    async def create(self, text: str) -> EmbeddingResult:
        response = await self._client.embeddings.create(
            model=settings.AI.EMBEDDING_MODEL, input=text
        )
        return EmbeddingResult(
            embedding=response.data[0].embedding,
            tokens=response.usage.total_tokens,
        )


embedding_client = EmbeddingClient()
