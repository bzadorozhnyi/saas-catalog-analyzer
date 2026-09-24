from app.api.v1.schemas.request import ExplainDuplicateRequest
from app.api.v1.schemas.response import ExplainDuplicateResponse
from app.services.duplicate_explanation_service import DuplicateExplanationService


class ExplainDuplicateUseCase:
    def __init__(self, service: DuplicateExplanationService) -> None:
        self._service = service

    async def execute(self, request: ExplainDuplicateRequest) -> ExplainDuplicateResponse:
        result = await self._service.explain(request.name_a, request.name_b)
        return ExplainDuplicateResponse(
            is_duplicate=result.is_duplicate,
            confidence=result.confidence,
            reasoning=result.reasoning,
            overlapping_features=result.overlapping_features,
        )
