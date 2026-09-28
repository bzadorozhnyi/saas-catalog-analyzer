from app.api.v1.schemas.response import SimilarItemResponse
from app.core.exceptions import NotFoundException
from app.services.catalog_service import CatalogService


class FindSimilarItemsUseCase:
    def __init__(self, service: CatalogService) -> None:
        self._service = service

    async def execute(self, item_id: int, limit: int) -> list[SimilarItemResponse]:
        items = await self._service.find_similar_items(item_id, limit)
        if items is None:
            raise NotFoundException(msg=f"Software item {item_id} not found")
        return [
            SimilarItemResponse(item_id=i.item_id, name=i.name, similarity=i.similarity)
            for i in items
        ]
