from app.api.v1.router import router
from app.api.v1.schemas.request import ExplainDuplicateRequest
from app.api.v1.schemas.response import ExplainDuplicateResponse
from app.dependency.use_case import ExplainDuplicateUseCaseDep


@router.post("/explain-duplicate")
async def explain_duplicate(
    request: ExplainDuplicateRequest, use_case: ExplainDuplicateUseCaseDep
) -> ExplainDuplicateResponse:
    return await use_case.execute(request)
