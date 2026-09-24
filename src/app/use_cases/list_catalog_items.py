from app.api.v1.schemas.response import CatalogItemResponse
from app.services.catalog_service import CatalogService


class ListCatalogItemsUseCase:
    def __init__(self, service: CatalogService):
        self._service = service

    async def execute(self) -> list[CatalogItemResponse]:
        items = await self._service.list_items()
        return [CatalogItemResponse.model_validate(item) for item in items]
