from typing import Annotated

from fastapi import Depends

from app.ai.embeddings import embedding_client
from app.core.config import settings
from app.dependency.db import DbSessionDep
from app.dependency.repository import (
    CatalogRepositoryDep,
    DuplicateRepositoryDep,
    EmbeddingCacheRepositoryDep,
    ReportDocumentRepositoryDep,
    RequestAttemptRepositoryDep,
    RequestRepositoryDep,
)
from app.dependency.s3 import S3ClientDep
from app.services.catalog_service import CatalogService
from app.services.classification_service import ClassificationService
from app.services.duplicate_detection_service import DuplicateDetectionService
from app.services.duplicate_explanation_service import DuplicateExplanationService
from app.services.embedding_service import EmbeddingService
from app.services.report_service import ReportService
from app.services.request_service import RequestService
from app.services.s3_storage_service import S3StorageService


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
    session: DbSessionDep,
    catalog_repository: CatalogRepositoryDep,
    duplicate_repository: DuplicateRepositoryDep,
) -> DuplicateDetectionService:
    return DuplicateDetectionService(session, catalog_repository, duplicate_repository)


DuplicateDetectionServiceDep = Annotated[
    DuplicateDetectionService, Depends(get_duplicate_detection_service)
]


def get_duplicate_explanation_service(
    session: DbSessionDep,
    catalog_repository: CatalogRepositoryDep,
    duplicate_repository: DuplicateRepositoryDep,
) -> DuplicateExplanationService:
    return DuplicateExplanationService(session, catalog_repository, duplicate_repository)


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


def get_s3_storage_service(client: S3ClientDep) -> S3StorageService:
    return S3StorageService(client, settings.S3.BUCKET_NAME)


S3StorageServiceDep = Annotated[S3StorageService, Depends(get_s3_storage_service)]


def get_report_service(
    repository: ReportDocumentRepositoryDep,
    s3_storage_service: S3StorageServiceDep,
) -> ReportService:
    return ReportService(repository, s3_storage_service)


ReportServiceDep = Annotated[ReportService, Depends(get_report_service)]
