from fastapi import status

from app.api.v1.router import router
from app.api.v1.schemas.request import CreateCatalogItemRequest
from app.api.v1.schemas.response import CatalogItemResponse
from app.dependency.use_case import CreateCatalogItemUseCaseDep


@router.post("/catalog", status_code=status.HTTP_201_CREATED)
async def create_catalog_item(
    request: CreateCatalogItemRequest, use_case: CreateCatalogItemUseCaseDep
) -> CatalogItemResponse:
    return await use_case.execute(request)
