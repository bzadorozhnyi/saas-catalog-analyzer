from typing import Annotated

from fastapi import Depends

from app.dependency.db import DbSessionDep
from app.repositories.catalog_repository import CatalogRepository
from app.repositories.embedding_cache_repository import EmbeddingCacheRepository
from app.repositories.request_attempt_repository import RequestAttemptRepository
from app.repositories.request_repository import RequestRepository


def get_catalog_repository(session: DbSessionDep) -> CatalogRepository:
    return CatalogRepository(session)


def get_embedding_cache_repository(session: DbSessionDep) -> EmbeddingCacheRepository:
    return EmbeddingCacheRepository(session)


def get_request_repository(session: DbSessionDep) -> RequestRepository:
    return RequestRepository(session)


def get_request_attempt_repository(session: DbSessionDep) -> RequestAttemptRepository:
    return RequestAttemptRepository(session)


CatalogRepositoryDep = Annotated[CatalogRepository, Depends(get_catalog_repository)]
EmbeddingCacheRepositoryDep = Annotated[
    EmbeddingCacheRepository, Depends(get_embedding_cache_repository)
]
RequestRepositoryDep = Annotated[RequestRepository, Depends(get_request_repository)]
RequestAttemptRepositoryDep = Annotated[
    RequestAttemptRepository, Depends(get_request_attempt_repository)
]
