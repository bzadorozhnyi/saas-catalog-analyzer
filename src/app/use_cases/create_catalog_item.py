from app.api.v1.schemas.request import CreateCatalogItemRequest
from app.api.v1.schemas.response import CatalogItemResponse
from app.services.catalog_service import CatalogService


class CreateCatalogItemUseCase:
    def __init__(self, service: CatalogService):
        self._service = service

    async def execute(self, request: CreateCatalogItemRequest) -> CatalogItemResponse:
        item = await self._service.create_item(
            name=request.name,
            description=request.description,
            category=request.category,
        )
        return CatalogItemResponse.model_validate(item)
