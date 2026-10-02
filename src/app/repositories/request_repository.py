import uuid
from datetime import UTC, datetime, timedelta
from typing import cast

from sqlalchemy import CursorResult, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func

from app.core.observability import current_trace_id
from app.enums.request_status_enum import RequestStatusEnum
from app.enums.request_type_enum import RequestTypeEnum
from app.models.request import Request


class RequestRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, request_type: RequestTypeEnum, payload: dict) -> Request:
        request = Request(
            id=uuid.uuid4(),
            request_type=request_type,
            payload=payload,
            trace_id=current_trace_id(),
        )
        self._session.add(request)
        return request

    async def get(self, request_id: uuid.UUID) -> Request | None:
        return await self._session.get(Request, request_id)

    async def list_pending(self, limit: int) -> list[Request]:
        stmt = (
            select(Request)
            .where(Request.status == RequestStatusEnum.PENDING)
            .order_by(Request.created_at)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def mark_queued(self, request_id: uuid.UUID) -> bool:
        stmt = (
            update(Request)
            .where(Request.id == request_id, Request.status == RequestStatusEnum.PENDING)
            .values(status=RequestStatusEnum.QUEUED)
        )
        result = cast(CursorResult, await self._session.execute(stmt))
        return result.rowcount == 1

    async def claim(
        self, request_id: uuid.UUID, worker_id: str, lock_duration: timedelta
    ) -> Request | None:
        # FAILED is claimable too — it isn't terminal. It means the last
        # attempt didn't work out; SQS's own redelivery (or a manual DLQ
        # redrive, which never touches this table) drives the next try.
        # FAILED rows have no active lock (fail() clears locked_by), so —
        # unlike the PROCESSING branch — there's no need to wait out a
        # lock: nothing is currently working on them.
        stmt = (
            update(Request)
            .where(
                Request.id == request_id,
                or_(
                    Request.status == RequestStatusEnum.QUEUED,
                    Request.status == RequestStatusEnum.FAILED,
                    (Request.status == RequestStatusEnum.PROCESSING)
                    & (Request.locked_until < func.now()),
                ),
            )
            .values(
                status=RequestStatusEnum.PROCESSING,
                locked_by=worker_id,
                locked_until=datetime.now(UTC) + lock_duration,
            )
            .returning(Request)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def extend_lock(
        self, request_id: uuid.UUID, worker_id: str, lock_duration: timedelta
    ) -> bool:
        stmt = (
            update(Request)
            .where(
                Request.id == request_id,
                Request.locked_by == worker_id,
                Request.status == RequestStatusEnum.PROCESSING,
            )
            .values(locked_until=datetime.now(UTC) + lock_duration)
        )
        result = cast(CursorResult, await self._session.execute(stmt))
        return result.rowcount == 1

    async def complete(self, request_id: uuid.UUID, worker_id: str, result_item_id: int) -> bool:
        stmt = (
            update(Request)
            .where(Request.id == request_id, Request.locked_by == worker_id)
            .values(
                status=RequestStatusEnum.COMPLETED,
                result_item_id=result_item_id,
                locked_by=None,
                locked_until=None,
            )
        )
        result = cast(CursorResult, await self._session.execute(stmt))
        return result.rowcount == 1

    async def fail(self, request_id: uuid.UUID, worker_id: str) -> bool:
        # Not terminal — see claim(). Whether this request gets another
        # attempt is entirely up to SQS (redelivery) or a manual DLQ
        # redrive; neither touches this table.
        stmt = (
            update(Request)
            .where(Request.id == request_id, Request.locked_by == worker_id)
            .values(status=RequestStatusEnum.FAILED, locked_by=None, locked_until=None)
        )
        result = cast(CursorResult, await self._session.execute(stmt))
        return result.rowcount == 1
