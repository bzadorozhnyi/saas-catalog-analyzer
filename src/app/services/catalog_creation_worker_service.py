import logfire
from sqlalchemy.ext.asyncio import AsyncSession

from app.dto.catalog import CatalogCreationPayload
from app.models.request import Request
from app.models.request_attempt import RequestAttempt
from app.repositories.catalog_repository import CatalogRepository
from app.services.classification_service import ClassificationService
from app.services.embedding_service import EmbeddingService
from app.services.request_service import RequestClaimLostError, RequestService


class CatalogCreationWorkerService:
    def __init__(
        self,
        session: AsyncSession,
        request_service: RequestService,
        catalog_repository: CatalogRepository,
        classification_service: ClassificationService,
        embedding_service: EmbeddingService,
        worker_id: str,
    ) -> None:
        self._session = session
        self._request_service = request_service
        self._catalog_repository = catalog_repository
        self._classification_service = classification_service
        self._embedding_service = embedding_service
        self._worker_id = worker_id

    async def process(self, request: Request, attempt: RequestAttempt) -> None:
        try:
            await self._execute_attempt(request, attempt)
        except RequestClaimLostError:
            await self._session.rollback()
            logfire.warning(
                "Lost claim on request {request_id}, another worker took over",
                request_id=request.id,
            )
        except Exception as error:
            logfire.exception("Attempt failed for request {request_id}", request_id=request.id)
            await self._session.rollback()
            await self._handle_failure(request, attempt, str(error))

    async def _execute_attempt(self, request: Request, attempt: RequestAttempt) -> None:
        payload = CatalogCreationPayload.model_validate(request.payload)
        classification = await self._classification_service.classify(
            payload.name, payload.description
        )
        embedding = await self._embedding_service.get_embedding(
            f"{payload.name}: {payload.description}"
        )
        item = await self._catalog_repository.create(
            name=payload.name,
            description=payload.description,
            category=classification.category,
            embedding=embedding,
        )
        await self._request_service.complete(
            request_id=request.id,
            worker_id=self._worker_id,
            attempt_id=attempt.id,
            result_item_id=item.id,
            success_message=f"Created software item {item.id} ({classification.category})",
            trace_id=None,
        )
        await self._session.commit()

    async def _handle_failure(
        self, request: Request, attempt: RequestAttempt, error_message: str
    ) -> None:
        try:
            await self._request_service.fail(
                request_id=request.id,
                worker_id=self._worker_id,
                attempt_id=attempt.id,
                error_message=error_message,
                trace_id=None,
            )
        except RequestClaimLostError:
            await self._session.rollback()
            logfire.warning(
                "Lost claim on request {request_id} while recording failure",
                request_id=request.id,
            )
        except Exception:
            logfire.exception(
                "Could not record failure for request {request_id} — DB may be unreachable",
                request_id=request.id,
            )
            raise
