from app.api.v1.router import router
from app.api.v1.schemas.request import ClassifyRequest
from app.api.v1.schemas.response import ClassifyResponse
from app.dependency.use_case import ClassifySoftwareUseCaseDep


@router.post("/classify")
async def classify(
    request: ClassifyRequest, use_case: ClassifySoftwareUseCaseDep
) -> ClassifyResponse:
    return await use_case.execute(request)
