from app.api.v1.router import router
from app.api.v1.schemas.response import SimilarItemResponse
from app.dependency.use_case import FindSimilarItemsUseCaseDep


@router.get("/catalog/{item_id}/similar")
async def find_similar_items(
    item_id: int, use_case: FindSimilarItemsUseCaseDep, limit: int = 5
) -> list[SimilarItemResponse]:
    return await use_case.execute(item_id, limit)
