from fastapi import status

from app.api.v1.router import router
from app.api.v1.schemas.request import GenerateReportRequest
from app.api.v1.schemas.response import GenerateReportAcceptedResponse
from app.dependency.use_case import GenerateReportUseCaseDep


@router.post("/generate-report", status_code=status.HTTP_202_ACCEPTED)
async def generate_report(
    payload: GenerateReportRequest, use_case: GenerateReportUseCaseDep
) -> GenerateReportAcceptedResponse:
    return await use_case.execute(payload)
