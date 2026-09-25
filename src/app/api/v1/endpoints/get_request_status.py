import uuid

from app.api.v1.router import router
from app.api.v1.schemas.response import RequestStatusResponse
from app.dependency.use_case import GetRequestStatusUseCaseDep


@router.get("/catalog/requests/{request_id}")
async def get_request_status(
    request_id: uuid.UUID, use_case: GetRequestStatusUseCaseDep
) -> RequestStatusResponse:
    return await use_case.execute(request_id)
