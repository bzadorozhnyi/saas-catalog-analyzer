from fastapi import Request

from app.api.v1.router import router
from app.api.v1.schemas.request import ExplainDuplicateRequest
from app.api.v1.schemas.response import ExplainDuplicateResponse
from app.core.rate_limiter import limiter
from app.dependency.use_case import ExplainDuplicateUseCaseDep


@router.post("/explain-duplicate")
@limiter.limit("10/minute")
async def explain_duplicate(
    request: Request,
    payload: ExplainDuplicateRequest,
    use_case: ExplainDuplicateUseCaseDep,
) -> ExplainDuplicateResponse:
    return await use_case.execute(payload)
