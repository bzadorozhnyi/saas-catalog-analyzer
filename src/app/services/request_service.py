import uuid
from datetime import timedelta

import logfire
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.enums.request_type_enum import RequestTypeEnum
from app.models.request import Request
from app.models.request_attempt import RequestAttempt
from app.repositories.request_attempt_repository import RequestAttemptRepository
from app.repositories.request_repository import RequestRepository


class RequestClaimLostError(Exception):
    """Raised when another worker took over the lock before this worker could persist its result."""


class RequestService:
    def __init__(
        self,
        session: AsyncSession,
        request_repository: RequestRepository,
        attempt_repository: RequestAttemptRepository,
    ) -> None:
        self._session = session
        self._request_repository = request_repository
        self._attempt_repository = attempt_repository

    async def create(self, request_type: RequestTypeEnum, payload: dict) -> Request:
        request = await self._request_repository.create(request_type, payload)
        try:
            await self._session.commit()
        except Exception:
            logfire.exception("Failed to commit new request")
            await self._session.rollback()
            raise
        return request

    async def list_pending_for_dispatch(self, limit: int) -> list[Request]:
        return await self._request_repository.list_pending(limit)

    async def mark_queued(self, request_id: uuid.UUID) -> bool:
        marked = await self._request_repository.mark_queued(request_id)
        try:
            await self._session.commit()
        except Exception:
            logfire.exception(
                "Failed to commit request {request_id} queued state", request_id=request_id
            )
            await self._session.rollback()
            raise
        return marked

    async def claim(
        self, request_id: uuid.UUID, worker_id: str
    ) -> tuple[Request, RequestAttempt] | None:
        lock_duration = timedelta(seconds=settings.WORKER.LOCK_DURATION_SECONDS)
        request = await self._request_repository.claim(request_id, worker_id, lock_duration)
        if request is None:
            return None

        attempt_number = await self._attempt_repository.count_for_request(request_id) + 1
        attempt = await self._attempt_repository.start(request_id, attempt_number)
        try:
            await self._session.commit()
        except Exception:
            logfire.exception(
                "Failed to commit claim for request {request_id}", request_id=request_id
            )
            await self._session.rollback()
            raise
        return request, attempt

    async def extend_lock(self, request_id: uuid.UUID, worker_id: str) -> bool:
        lock_duration = timedelta(seconds=settings.WORKER.LOCK_DURATION_SECONDS)
        extended = await self._request_repository.extend_lock(request_id, worker_id, lock_duration)
        try:
            await self._session.commit()
        except Exception:
            logfire.exception(
                "Failed to commit lock extension for request {request_id}", request_id=request_id
            )
            await self._session.rollback()
            raise
        return extended

    async def complete(
        self,
        request_id: uuid.UUID,
        worker_id: str,
        attempt_id: uuid.UUID,
        result_item_id: int,
        success_message: str,
        trace_id: str | None,
    ) -> None:
        # No commit here on purpose: the caller (worker) stages a business-specific
        # write (the created software_item) in the same session, and must commit
        # once, after this call, so both succeed or both roll back together.
        completed = await self._request_repository.complete(request_id, worker_id, result_item_id)
        if not completed:
            raise RequestClaimLostError(f"Lock for request {request_id} was lost before completion")
        await self._attempt_repository.succeed(attempt_id, success_message, trace_id)

    async def fail(
        self,
        request_id: uuid.UUID,
        worker_id: str,
        attempt_id: uuid.UUID,
        error_message: str,
        trace_id: str | None,
    ) -> None:
        attempt_count = await self._attempt_repository.count_for_request(request_id)
        is_terminal = attempt_count >= settings.WORKER.MAX_ATTEMPTS
        updated = await self._request_repository.retry_or_fail(request_id, worker_id, is_terminal)
        if not updated:
            raise RequestClaimLostError(
                f"Lock for request {request_id} was lost before failure handling"
            )
        await self._attempt_repository.fail(attempt_id, error_message, trace_id)
        try:
            await self._session.commit()
        except Exception:
            logfire.exception(
                "Failed to commit failure handling for request {request_id}", request_id=request_id
            )
            await self._session.rollback()
            raise
