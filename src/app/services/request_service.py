import uuid
from datetime import timedelta
from enum import StrEnum

import logfire
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.enums.request_status_enum import RequestStatusEnum
from app.enums.request_type_enum import RequestTypeEnum
from app.models.request import Request
from app.models.request_attempt import RequestAttempt
from app.repositories.request_attempt_repository import RequestAttemptRepository
from app.repositories.request_repository import RequestRepository


class RequestClaimLostError(Exception):
    """Raised when another worker took over the lock before this worker could persist its result."""


class ClaimOutcome(StrEnum):
    """What the caller should do about the SQS message when `claim()`
    doesn't return a claimed `(Request, RequestAttempt)` pair.

    "Not claimed" used to mean one thing to callers (safe to delete the SQS
    message) — it actually covers two different situations:

    NOT_YET_QUEUED: the row is still PENDING. The dispatcher's SQS send and
    its mark_queued commit aren't one atomic operation, so a message can
    legitimately arrive before the row is actually claimable yet. Not a
    duplicate — leave the message alone for SQS's own redelivery.

    UNCLAIMABLE: the row doesn't exist, is already COMPLETED, or is
    PROCESSING under another worker's still-live lock — nothing further is
    needed from this message; safe to delete.
    """

    NOT_YET_QUEUED = "NOT_YET_QUEUED"
    UNCLAIMABLE = "UNCLAIMABLE"


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

    async def get(self, request_id: uuid.UUID) -> Request | None:
        return await self._request_repository.get(request_id)

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
    ) -> tuple[Request, RequestAttempt] | ClaimOutcome:
        lock_duration = timedelta(seconds=settings.WORKER.LOCK_DURATION_SECONDS)
        request = await self._request_repository.claim(request_id, worker_id, lock_duration)

        if request is None:
            # Lock the row so nothing (dispatcher's mark_queued, another
            # worker's complete()/fail()) can change it while we work out
            # why the attempt above missed, then decide — or retry right
            # there — against an accurate, race-free snapshot.
            status = await self._request_repository.get_status_for_update(request_id)
            if status in (
                RequestStatusEnum.QUEUED,
                RequestStatusEnum.FAILED,
                RequestStatusEnum.PROCESSING,
            ):
                # Became claimable (or its lock expired) in the gap above —
                # still holding the row lock, so this is guaranteed to see
                # the same state just read.
                request = await self._request_repository.claim(
                    request_id, worker_id, lock_duration
                )

            if request is None:
                outcome = (
                    ClaimOutcome.NOT_YET_QUEUED
                    if status == RequestStatusEnum.PENDING
                    else ClaimOutcome.UNCLAIMABLE
                )
                try:
                    await self._session.commit()  # releases the FOR UPDATE row lock
                except Exception:
                    logfire.exception(
                        "Failed to release claim lock for request {request_id}",
                        request_id=request_id,
                    )
                    await self._session.rollback()
                    raise
                return outcome

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
        # Not terminal — see RequestRepository.claim()/fail(). How many more
        # times this gets tried is SQS's call (redelivery + RedrivePolicy),
        # not ours; we just record what happened.
        updated = await self._request_repository.fail(request_id, worker_id)
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
