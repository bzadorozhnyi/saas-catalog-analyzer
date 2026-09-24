from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.embedding_cache import EmbeddingCache


class EmbeddingCacheRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, content_hash: str) -> list[float] | None:
        result = await self._session.execute(
            select(EmbeddingCache.embedding).where(EmbeddingCache.content_hash == content_hash)
        )
        embedding = result.scalar_one_or_none()
        return list(embedding) if embedding is not None else None

    async def set(self, content_hash: str, embedding: list[float]) -> None:
        stmt = (
            insert(EmbeddingCache)
            .values(content_hash=content_hash, embedding=embedding)
            .on_conflict_do_nothing(index_elements=[EmbeddingCache.content_hash])
        )
        await self._session.execute(stmt)
