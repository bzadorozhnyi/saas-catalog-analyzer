import asyncio
import uuid

import logfire

from app.consumers.catalog_creation_consumer import CatalogCreationConsumer
from app.core.config import settings
from app.core.llm_call_batcher import llm_call_batcher
from app.core.observability import configure_logfire
from app.core.sqs import build_queue_url, sqs_client
from app.services.sqs_service import SQSService

MAX_MESSAGES = 5
WAIT_SECONDS = 20
WORKER_ID = f"worker-{uuid.uuid4()}"


async def main() -> None:
    configure_logfire()
    await llm_call_batcher.start()
    queue_url = build_queue_url(settings.SQS.QUEUE_NAME, settings.SQS.ACCOUNT_ID)

    try:
        async with sqs_client() as client:
            sqs_service = SQSService(client, queue_url)
            consumer = CatalogCreationConsumer(sqs_service, WORKER_ID)
            while True:
                try:
                    await consumer.run_once(MAX_MESSAGES, WAIT_SECONDS)
                except Exception:
                    logfire.exception("Failed to receive messages from SQS")
    finally:
        await llm_call_batcher.stop()


if __name__ == "__main__":
    asyncio.run(main())
