import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.report_document import ReportDocument


class ReportDocumentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_request_id(self, request_id: uuid.UUID) -> ReportDocument | None:
        stmt = select(ReportDocument).where(ReportDocument.request_id == request_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()
