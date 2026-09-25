from fastapi import Request

from app.api.v1.router import router
from app.api.v1.schemas.request import ClassifyRequest
from app.api.v1.schemas.response import ClassifyResponse
from app.core.rate_limiter import limiter
from app.dependency.use_case import ClassifySoftwareUseCaseDep


@router.post("/classify")
@limiter.limit("10/minute")
async def classify(
    request: Request, payload: ClassifyRequest, use_case: ClassifySoftwareUseCaseDep
) -> ClassifyResponse:
    return await use_case.execute(payload)
