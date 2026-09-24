from openai import AsyncOpenAI

from app.core.config import settings


class EmbeddingClient:
    def __init__(self) -> None:
        self._client = AsyncOpenAI(api_key=settings.AI.OPENAI_API_KEY)

    async def create(self, text: str) -> list[float]:
        response = await self._client.embeddings.create(
            model=settings.AI.EMBEDDING_MODEL, input=text
        )
        return response.data[0].embedding


embedding_client = EmbeddingClient()
