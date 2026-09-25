from app.api.v1.schemas.request import CreateCatalogItemRequest
from app.api.v1.schemas.response import CreateCatalogItemAcceptedResponse
from app.enums.request_type_enum import RequestTypeEnum
from app.services.request_service import RequestService


class CreateCatalogItemUseCase:
    def __init__(self, service: RequestService) -> None:
        self._service = service

    async def execute(self, request: CreateCatalogItemRequest) -> CreateCatalogItemAcceptedResponse:
        created_request = await self._service.create(
            request_type=RequestTypeEnum.CATALOG_CREATION,
            payload={"name": request.name, "description": request.description},
        )
        return CreateCatalogItemAcceptedResponse(request_id=created_request.id)
