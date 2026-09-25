import asyncio

import logfire

from app.core.config import settings
from app.core.observability import configure_logfire
from app.core.sqs import build_queue_url, sqs_client
from app.db.session import async_session_factory
from app.repositories.request_attempt_repository import RequestAttemptRepository
from app.repositories.request_repository import RequestRepository
from app.services.request_service import RequestService
from app.services.sqs_service import SQSService

POLL_INTERVAL_SECONDS = 5
BATCH_SIZE = 10


async def dispatch_once(sqs_service: SQSService) -> None:
    async with async_session_factory() as session:
        request_service = RequestService(
            session, RequestRepository(session), RequestAttemptRepository(session)
        )
        pending = await request_service.list_pending_for_dispatch(BATCH_SIZE)
        for request in pending:
            try:
                await sqs_service.send_message({"request_id": str(request.id)})
                await request_service.mark_queued(request.id)
            except Exception:
                logfire.exception(
                    "Failed to dispatch request {request_id} to SQS", request_id=request.id
                )


async def main() -> None:
    configure_logfire()
    queue_url = build_queue_url(settings.SQS.QUEUE_NAME, settings.SQS.ACCOUNT_ID)

    async with sqs_client() as client:
        sqs_service = SQSService(client, queue_url)
        while True:
            try:
                await dispatch_once(sqs_service)
            except Exception:
                logfire.exception("Dispatch cycle failed while listing pending requests")
            await asyncio.sleep(POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    asyncio.run(main())
