from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import SoftwareCategory
from app.models.software_item import SoftwareItem


class CatalogRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

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
        self._session.add(item)
        await self._session.flush()
        return item

    async def list(self) -> list[SoftwareItem]:
        result = await self._session.execute(select(SoftwareItem))
        return list(result.scalars().all())

    async def get(self, item_id: int) -> SoftwareItem | None:
        return await self._session.get(SoftwareItem, item_id)
