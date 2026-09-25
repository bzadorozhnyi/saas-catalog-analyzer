import asyncio
import json
import uuid
from datetime import timedelta

import logfire

from app.ai.embeddings import embedding_client
from app.core.config import settings
from app.db.session import async_session_factory
from app.repositories.catalog_repository import CatalogRepository
from app.repositories.embedding_cache_repository import EmbeddingCacheRepository
from app.repositories.request_attempt_repository import RequestAttemptRepository
from app.repositories.request_repository import RequestRepository
from app.services.catalog_creation_worker_service import CatalogCreationWorkerService
from app.services.classification_service import ClassificationService
from app.services.embedding_service import EmbeddingService
from app.services.request_service import RequestService
from app.services.sqs_service import SQSService


class CatalogCreationConsumer:
    def __init__(self, sqs_service: SQSService, worker_id: str) -> None:
        self._sqs_service = sqs_service
        self._worker_id = worker_id

    async def run_once(self, max_messages: int, wait_seconds: int) -> None:
        messages = await self._sqs_service.receive_messages(max_messages, wait_seconds)
        await asyncio.gather(*(self._handle_message(message) for message in messages))

    async def _handle_message(self, message: dict) -> None:
        receipt_handle = message["ReceiptHandle"]
        try:
            body = json.loads(message["Body"])
            request_id = uuid.UUID(body["request_id"])
        except Exception:
            logfire.exception(
                "Malformed SQS message, deleting: {body}", body=message.get("Body")
            )
            await self._sqs_service.delete_message(receipt_handle)
            return

        async with async_session_factory() as session:
            request_service = RequestService(
                session, RequestRepository(session), RequestAttemptRepository(session)
            )
            claimed = await request_service.claim(request_id, self._worker_id)
            if claimed is None:
                await self._sqs_service.delete_message(receipt_handle)
                return
            request, attempt = claimed

            worker_service = CatalogCreationWorkerService(
                session=session,
                request_service=request_service,
                catalog_repository=CatalogRepository(session),
                classification_service=ClassificationService(),
                embedding_service=EmbeddingService(
                    embedding_client, EmbeddingCacheRepository(session)
                ),
                worker_id=self._worker_id,
            )

            heartbeat_task = asyncio.create_task(self._heartbeat(request_id))
            try:
                await worker_service.process(request, attempt)
            except Exception:
                # process() only re-raises when it could not even persist the
                # failure (e.g. DB unreachable) — leave the message for redelivery.
                heartbeat_task.cancel()
                return
            finally:
                heartbeat_task.cancel()

        await self._sqs_service.delete_message(receipt_handle)

    async def _heartbeat(self, request_id: uuid.UUID) -> None:
        lock_duration = timedelta(seconds=settings.WORKER.LOCK_DURATION_SECONDS)
        try:
            while True:
                await asyncio.sleep(settings.WORKER.HEARTBEAT_INTERVAL_SECONDS)
                async with async_session_factory() as session:
                    extended = await RequestRepository(session).extend_lock(
                        request_id, self._worker_id, lock_duration
                    )
                    await session.commit()
                if not extended:
                    # Lock already lost to another worker; nothing left to extend.
                    return
        except asyncio.CancelledError:
            pass
        except Exception:
            logfire.exception("Heartbeat failed for request {request_id}", request_id=request_id)
