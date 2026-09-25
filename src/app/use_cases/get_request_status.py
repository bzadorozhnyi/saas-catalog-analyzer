import uuid

from app.api.v1.schemas.response import RequestStatusResponse
from app.core.exceptions import NotFoundException
from app.repositories.request_repository import RequestRepository


class GetRequestStatusUseCase:
    def __init__(self, repository: RequestRepository) -> None:
        self._repository = repository

    async def execute(self, request_id: uuid.UUID) -> RequestStatusResponse:
        request = await self._repository.get(request_id)
        if request is None:
            raise NotFoundException(msg=f"Request {request_id} not found")
        return RequestStatusResponse(
            request_id=request.id,
            status=request.status,
            result_item_id=request.result_item_id,
        )
