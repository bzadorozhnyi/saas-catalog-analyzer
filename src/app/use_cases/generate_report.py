from app.api.v1.schemas.request import GenerateReportRequest
from app.api.v1.schemas.response import GenerateReportAcceptedResponse
from app.enums.request_type_enum import RequestTypeEnum
from app.services.request_service import RequestService


class GenerateReportUseCase:
    def __init__(self, service: RequestService) -> None:
        self._service = service

    async def execute(self, request: GenerateReportRequest) -> GenerateReportAcceptedResponse:
        created_request = await self._service.create(
            request_type=RequestTypeEnum.GENERATE_REPORT,
            payload={
                # Must match a (kind, version) arm in report-service's
                # reporting::registry::build_report.
                "report_kind": "duplicate_detection",
                "report_version": request.report_version,
                "check_id": str(request.check_id),
            },
        )
        return GenerateReportAcceptedResponse(request_id=created_request.id)
