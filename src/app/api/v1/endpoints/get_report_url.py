import uuid

from app.api.v1.router import router
from app.api.v1.schemas.response import ReportUrlResponse
from app.dependency.use_case import GetReportUrlUseCaseDep


@router.get("/reports/{request_id}/url")
async def get_report_url(
    request_id: uuid.UUID, use_case: GetReportUrlUseCaseDep
) -> ReportUrlResponse:
    return await use_case.execute(request_id)
