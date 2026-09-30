import asyncio
import json
import uuid
from collections import Counter
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

import logfire
import typer

from app.core.config import settings
from app.core.observability import configure_logfire
from app.core.sqs import build_queue_url, sqs_client
from app.db.session import async_session_factory
from app.enums.request_status_enum import RequestStatusEnum
from app.repositories.request_attempt_repository import RequestAttemptRepository
from app.repositories.request_repository import RequestRepository
from app.services.request_service import RequestService
from app.services.sqs_service import SQSService

app = typer.Typer()


class Decision(StrEnum):
    REDRIVE = "redrive"
    SKIP_IN_FLIGHT = "skip_in_flight"
    SKIP_UNEXPECTED_STATUS = "skip_unexpected_status"
    PURGE_COMPLETED = "purge_completed"
    SKIP_UNKNOWN_REQUEST = "skip_unknown_request"
    SKIP_MALFORMED = "skip_malformed"


_SKIP_DECISIONS = {
    Decision.SKIP_IN_FLIGHT,
    Decision.SKIP_UNEXPECTED_STATUS,
    Decision.SKIP_UNKNOWN_REQUEST,
    Decision.SKIP_MALFORMED,
}


async def _decide(request_service: RequestService, request_id: uuid.UUID) -> Decision:
    request = await request_service.get(request_id)
    if request is None:
        return Decision.SKIP_UNKNOWN_REQUEST

    if request.status == RequestStatusEnum.QUEUED:
        return Decision.REDRIVE

    if request.status == RequestStatusEnum.PROCESSING:
        lock_expired = request.locked_until is not None and request.locked_until < datetime.now(UTC)
        return Decision.REDRIVE if lock_expired else Decision.SKIP_IN_FLIGHT

    # FAILED isn't terminal (see RequestRepository.claim()) — a DLQ message
    # for one just means SQS exhausted its own attempts. Redriving it is
    # exactly as safe as any other retry: worst case, it fails again and
    # lands back here. No DB write needed either way.
    if request.status == RequestStatusEnum.FAILED:
        return Decision.REDRIVE

    if request.status == RequestStatusEnum.COMPLETED:
        return Decision.PURGE_COMPLETED

    # PENDING should never have a live DLQ message in the first place.
    return Decision.SKIP_UNEXPECTED_STATUS


async def _apply_decision(
    decision: Decision,
    body: dict[str, Any],
    receipt_handle: str,
    request_id: uuid.UUID,
    main_queue: SQSService,
    dlq: SQSService,
) -> None:
    if decision == Decision.REDRIVE:
        await main_queue.send_message(body)
        await dlq.delete_message(receipt_handle)
        logfire.info("Redrove DLQ message for request {request_id}", request_id=request_id)
    elif decision == Decision.PURGE_COMPLETED:
        await dlq.delete_message(receipt_handle)
    # SKIP_* decisions leave the message in the DLQ untouched.


async def _handle_message(
    message: dict[str, Any], main_queue: SQSService, dlq: SQSService, *, apply: bool
) -> Decision:
    receipt_handle = message["ReceiptHandle"]
    body_raw = message.get("Body", "")
    try:
        body = json.loads(body_raw)
        request_id = uuid.UUID(body["request_id"])
    except Exception:
        logfire.exception("Malformed DLQ message body: {body}", body=body_raw)
        typer.echo(f"[{Decision.SKIP_MALFORMED.value}] body={body_raw!r}")
        return Decision.SKIP_MALFORMED

    async with async_session_factory() as session:
        request_service = RequestService(
            session, RequestRepository(session), RequestAttemptRepository(session)
        )
        decision = await _decide(request_service, request_id)
        typer.echo(f"[{decision.value}] request_id={request_id}")

        if apply and decision not in _SKIP_DECISIONS:
            await _apply_decision(decision, body, receipt_handle, request_id, main_queue, dlq)

    return decision


async def _redrive(*, apply: bool, limit: int) -> None:
    configure_logfire()
    # Only handles the catalog-creation queue/DLQ for now; report-generation
    # redrive can reuse this once that consumer exists.
    main_queue_url = build_queue_url(settings.SQS.CATALOG.QUEUE_NAME, settings.SQS.ACCOUNT_ID)
    dlq_url = build_queue_url(settings.SQS.CATALOG.DLQ_NAME, settings.SQS.ACCOUNT_ID)

    counters: Counter[str] = Counter()

    async with sqs_client() as client:
        main_queue = SQSService(client, main_queue_url)
        dlq = SQSService(client, dlq_url)

        while counters.total() < limit:
            try:
                messages = await dlq.receive_messages(
                    max_messages=min(10, limit - counters.total()), wait_seconds=1
                )
            except Exception:
                logfire.exception("Failed to receive messages from DLQ, stopping this run")
                typer.echo("Could not reach SQS, stopping. See logs for details.", err=True)
                break

            if not messages:
                break

            for message in messages:
                try:
                    decision = await _handle_message(message, main_queue, dlq, apply=apply)
                except Exception:
                    logfire.exception("Failed to handle a DLQ message")
                    typer.echo("  error handling this message, see logs; continuing", err=True)
                    counters["errors"] += 1
                    continue

                counters["skipped" if decision in _SKIP_DECISIONS else "succeeded"] += 1

    mode = "applied" if apply else "dry-run, use --apply to act"
    typer.echo(
        f"Done ({mode}): {counters['succeeded']} succeeded, "
        f"{counters['skipped']} skipped, {counters['errors']} errors"
    )
    if counters["errors"]:
        typer.echo(
            "Some messages failed to process — check logs, fix the issue, and rerun.", err=True
        )


@app.command()
def redrive(
    apply: bool = typer.Option(
        False, "--apply", help="Actually perform changes; without it, only prints decisions."
    ),
    limit: int = typer.Option(50, "--limit", help="Max DLQ messages to process in this run."),
) -> None:
    asyncio.run(_redrive(apply=apply, limit=limit))


if __name__ == "__main__":
    app()
