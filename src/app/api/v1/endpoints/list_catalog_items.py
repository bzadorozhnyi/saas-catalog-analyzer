from app.api.v1.router import router
from app.api.v1.schemas.response import CatalogItemResponse
from app.dependency.use_case import ListCatalogItemsUseCaseDep


@router.get("/catalog")
async def list_catalog_items(use_case: ListCatalogItemsUseCaseDep) -> list[CatalogItemResponse]:
    return await use_case.execute()
