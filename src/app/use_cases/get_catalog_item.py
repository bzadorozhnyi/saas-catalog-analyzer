from fastapi import HTTPException, status

from app.api.v1.schemas.response import CatalogItemResponse
from app.services.catalog_service import CatalogService


class GetCatalogItemUseCase:
    def __init__(self, service: CatalogService):
        self._service = service

    async def execute(self, item_id: int) -> CatalogItemResponse:
        item = await self._service.get_item(item_id)
        if item is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Software item {item_id} not found",
            )
        return CatalogItemResponse.model_validate(item)
