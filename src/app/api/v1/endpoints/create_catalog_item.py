from fastapi import status

from app.api.v1.router import router
from app.api.v1.schemas.request import CreateCatalogItemRequest
from app.api.v1.schemas.response import CreateCatalogItemAcceptedResponse
from app.dependency.use_case import CreateCatalogItemUseCaseDep


@router.post("/catalog", status_code=status.HTTP_202_ACCEPTED)
async def create_catalog_item(
    payload: CreateCatalogItemRequest, use_case: CreateCatalogItemUseCaseDep
) -> CreateCatalogItemAcceptedResponse:
    return await use_case.execute(payload)
