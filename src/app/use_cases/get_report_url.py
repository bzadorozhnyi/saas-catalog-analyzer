import uuid

from app.api.v1.schemas.response import ReportUrlResponse
from app.services.report_service import ReportService


class GetReportUrlUseCase:
    def __init__(self, service: ReportService) -> None:
        self._service = service

    async def execute(self, request_id: uuid.UUID) -> ReportUrlResponse:
        url = await self._service.get_download_url(request_id)
        return ReportUrlResponse(url=url)
