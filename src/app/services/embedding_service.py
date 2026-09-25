import hashlib
import time

from app.ai.embeddings import EmbeddingClient
from app.core.config import settings
from app.core.llm_call_batcher import log_llm_call
from app.enums.llm_call_purpose_enum import LlmCallPurposeEnum
from app.enums.llm_call_status_enum import LlmCallStatusEnum
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

        started_at = time.monotonic()
        try:
            result = await self._client.create(text)
        except Exception:
            log_llm_call(
                purpose=LlmCallPurposeEnum.EMBEDDING,
                model=settings.AI.EMBEDDING_MODEL,
                input_tokens=0,
                output_tokens=None,
                latency_ms=int((time.monotonic() - started_at) * 1000),
                status=LlmCallStatusEnum.ERROR,
            )
            raise

        log_llm_call(
            purpose=LlmCallPurposeEnum.EMBEDDING,
            model=settings.AI.EMBEDDING_MODEL,
            input_tokens=result.tokens,
            output_tokens=None,
            latency_ms=int((time.monotonic() - started_at) * 1000),
            status=LlmCallStatusEnum.SUCCESS,
        )
        await self._cache_repository.set(content_hash, result.embedding)
        return result.embedding
