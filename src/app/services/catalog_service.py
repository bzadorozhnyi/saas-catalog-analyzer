from sqlalchemy.ext.asyncio import AsyncSession

from app.dto.catalog import SimilarItem
from app.enums.software_category_enum import SoftwareCategoryEnum
from app.models.software_item import SoftwareItem
from app.repositories.catalog_repository import CatalogRepository
from app.services.embedding_service import EmbeddingService


class CatalogService:
    def __init__(
        self,
        session: AsyncSession,
        repository: CatalogRepository,
        embedding_service: EmbeddingService,
    ):
        self._session = session
        self._repository = repository
        self._embedding_service = embedding_service

    async def create_item(
        self, name: str, description: str, category: SoftwareCategoryEnum
    ) -> SoftwareItem:
        embedding = await self._embedding_service.get_embedding(f"{name}: {description}")
        item = await self._repository.create(
            name=name, description=description, category=category, embedding=embedding
        )
        await self._session.commit()
        return item

    async def list_items(self) -> list[SoftwareItem]:
        return await self._repository.list_all()

    async def get_item(self, item_id: int) -> SoftwareItem | None:
        return await self._repository.get(item_id)

    async def find_similar_items(self, item_id: int, limit: int) -> list[SimilarItem] | None:
        item = await self._repository.get(item_id)
        if item is None:
            return None
        return await self._repository.find_nearest(item.id, item.embedding, limit)
