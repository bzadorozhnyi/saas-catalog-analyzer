import uuid

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.enums.attempt_status_enum import AttemptStatusEnum
from app.models.request_attempt import RequestAttempt


class RequestAttemptRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def count_for_request(self, request_id: uuid.UUID) -> int:
        stmt = select(func.count()).select_from(RequestAttempt).where(
            RequestAttempt.request_id == request_id
        )
        result = await self._session.execute(stmt)
        return result.scalar_one()

    async def start(self, request_id: uuid.UUID, attempt_number: int) -> RequestAttempt:
        attempt = RequestAttempt(
            id=uuid.uuid4(),
            request_id=request_id,
            attempt_number=attempt_number,
            status=AttemptStatusEnum.STARTED,
        )
        self._session.add(attempt)
        return attempt

    async def succeed(
        self, attempt_id: uuid.UUID, success_message: str, trace_id: str | None
    ) -> None:
        stmt = (
            update(RequestAttempt)
            .where(RequestAttempt.id == attempt_id)
            .values(
                status=AttemptStatusEnum.SUCCEEDED,
                success_message=success_message,
                trace_id=trace_id,
                finished_at=func.now(),
            )
        )
        await self._session.execute(stmt)

    async def fail(self, attempt_id: uuid.UUID, error_message: str, trace_id: str | None) -> None:
        stmt = (
            update(RequestAttempt)
            .where(RequestAttempt.id == attempt_id)
            .values(
                status=AttemptStatusEnum.FAILED,
                error_message=error_message,
                trace_id=trace_id,
                finished_at=func.now(),
            )
        )
        await self._session.execute(stmt)
