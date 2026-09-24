from app.api.v1.schemas.request import FindDuplicatesRequest
from app.api.v1.schemas.response import DuplicatePairResponse
from app.services.duplicate_detection_service import DuplicateDetectionService


class FindDuplicatesUseCase:
    def __init__(self, service: DuplicateDetectionService) -> None:
        self._service = service

    async def execute(
        self,
        request: FindDuplicatesRequest,
        duplicate_threshold: float,
        review_threshold: float,
    ) -> list[DuplicatePairResponse]:
        return await self._service.find_duplicates(
            request.subscription_names, duplicate_threshold, review_threshold
        )
