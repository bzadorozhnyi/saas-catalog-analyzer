from app.api.v1.router import router
from app.api.v1.schemas.request import FindDuplicatesRequest
from app.api.v1.schemas.response import DuplicatePairResponse
from app.dependency.use_case import FindDuplicatesUseCaseDep


@router.post("/find-duplicates")
async def find_duplicates(
    payload: FindDuplicatesRequest,
    use_case: FindDuplicatesUseCaseDep,
    # Empirically calibrated on text-embedding-3-small over short SaaS product
    # descriptions: same-category pairs measured 0.588-0.812, different-category
    # pairs topped out at 0.560.
    duplicate_threshold: float = 0.65,
    review_threshold: float = 0.55,
) -> list[DuplicatePairResponse]:
    return await use_case.execute(payload, duplicate_threshold, review_threshold)
