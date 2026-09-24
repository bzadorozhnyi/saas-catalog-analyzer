from app.api.v1.schemas.request import ClassifyRequest
from app.api.v1.schemas.response import ClassifyResponse
from app.services.classification_service import ClassificationService


class ClassifySoftwareUseCase:
    def __init__(self, service: ClassificationService) -> None:
        self._service = service

    async def execute(self, request: ClassifyRequest) -> ClassifyResponse:
        result = await self._service.classify(request.name, request.description)
        return ClassifyResponse(
            category=result.category,
            confidence=result.confidence,
            reasoning=result.reasoning,
        )
