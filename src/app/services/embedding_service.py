import hashlib

from app.ai.embeddings import EmbeddingClient
from app.repositories.embedding_cache_repository import EmbeddingCacheRepository


class EmbeddingService:
    def __init__(
        self, client: EmbeddingClient, cache_repository: EmbeddingCacheRepository
    ) -> None:
        self._client = client
        self._cache_repository = cache_repository

    async def get_embedding(self, text: str) -> list[float]:
        content_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()

        cached = await self._cache_repository.get(content_hash)
        if cached is not None:
            return cached

        embedding = await self._client.create(text)
        await self._cache_repository.set(content_hash, embedding)
        return embedding
