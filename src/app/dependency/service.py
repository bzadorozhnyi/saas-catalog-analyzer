from typing import Annotated

from fastapi import Depends

from app.ai.embeddings import embedding_client
from app.dependency.db import DbSessionDep
from app.dependency.repository import (
    CatalogRepositoryDep,
    EmbeddingCacheRepositoryDep,
    RequestAttemptRepositoryDep,
    RequestRepositoryDep,
)
from app.services.catalog_service import CatalogService
from app.services.classification_service import ClassificationService
from app.services.duplicate_detection_service import DuplicateDetectionService
from app.services.duplicate_explanation_service import DuplicateExplanationService
from app.services.embedding_service import EmbeddingService
from app.services.request_service import RequestService


def get_classification_service() -> ClassificationService:
    return ClassificationService()


def get_embedding_service(cache_repository: EmbeddingCacheRepositoryDep) -> EmbeddingService:
    return EmbeddingService(embedding_client, cache_repository)


ClassificationServiceDep = Annotated[ClassificationService, Depends(get_classification_service)]
EmbeddingServiceDep = Annotated[EmbeddingService, Depends(get_embedding_service)]


def get_catalog_service(
    session: DbSessionDep,
    repository: CatalogRepositoryDep,
    embedding_service: EmbeddingServiceDep,
) -> CatalogService:
    return CatalogService(session, repository, embedding_service)


CatalogServiceDep = Annotated[CatalogService, Depends(get_catalog_service)]


def get_duplicate_detection_service(
    repository: CatalogRepositoryDep,
) -> DuplicateDetectionService:
    return DuplicateDetectionService(repository)


DuplicateDetectionServiceDep = Annotated[
    DuplicateDetectionService, Depends(get_duplicate_detection_service)
]


def get_duplicate_explanation_service(
    repository: CatalogRepositoryDep,
) -> DuplicateExplanationService:
    return DuplicateExplanationService(repository)


DuplicateExplanationServiceDep = Annotated[
    DuplicateExplanationService, Depends(get_duplicate_explanation_service)
]


def get_request_service(
    session: DbSessionDep,
    request_repository: RequestRepositoryDep,
    attempt_repository: RequestAttemptRepositoryDep,
) -> RequestService:
    return RequestService(session, request_repository, attempt_repository)


RequestServiceDep = Annotated[RequestService, Depends(get_request_service)]
