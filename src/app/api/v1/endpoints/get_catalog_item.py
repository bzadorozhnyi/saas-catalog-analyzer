from app.api.v1.router import router
from app.api.v1.schemas.response import CatalogItemResponse
from app.dependency.use_case import GetCatalogItemUseCaseDep


@router.get("/catalog/{item_id}")
async def get_catalog_item(
    item_id: int, use_case: GetCatalogItemUseCaseDep
) -> CatalogItemResponse:
    return await use_case.execute(item_id)
