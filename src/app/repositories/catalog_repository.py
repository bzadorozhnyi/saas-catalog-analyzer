import asyncio

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.dto.catalog import SimilarPair
from app.models.category import SoftwareCategory
from app.models.software_item import SoftwareItem


class CatalogRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._lock = asyncio.Lock()

    async def create(
        self,
        name: str,
        description: str,
        category: SoftwareCategory,
        embedding: list[float],
    ) -> SoftwareItem:
        item = SoftwareItem(
            name=name,
            description=description,
            category=category,
            embedding=embedding,
        )
        async with self._lock:
            self._session.add(item)
            await self._session.flush()
        return item

    async def list_all(self) -> list[SoftwareItem]:
        async with self._lock:
            result = await self._session.execute(select(SoftwareItem))
        return list(result.scalars().all())

    async def get(self, item_id: int) -> SoftwareItem | None:
        async with self._lock:
            return await self._session.get(SoftwareItem, item_id)

    async def get_by_name(self, name: str) -> SoftwareItem | None:
        async with self._lock:
            result = await self._session.execute(
                select(SoftwareItem).where(SoftwareItem.name == name)
            )
        return result.scalar_one_or_none()

    async def list_by_names(self, names: list[str]) -> list[SoftwareItem]:
        async with self._lock:
            result = await self._session.execute(
                select(SoftwareItem).where(SoftwareItem.name.in_(names))
            )
        return list(result.scalars().all())

    async def find_similar_pairs(
        self, names: list[str], min_similarity: float
    ) -> list[SimilarPair]:
        item_a = aliased(SoftwareItem)
        item_b = aliased(SoftwareItem)
        similarity = (1 - item_a.embedding.cosine_distance(item_b.embedding)).label("similarity")

        stmt = (
            select(item_a.name, item_b.name, similarity)
            .join(item_b, item_a.id < item_b.id)
            .where(item_a.name.in_(names), item_b.name.in_(names))
            .where(similarity >= min_similarity)
            .order_by(similarity.desc())
        )
        async with self._lock:
            result = await self._session.execute(stmt)
        return [SimilarPair(*row) for row in result.all()]
