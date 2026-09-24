from typing import Annotated

from fastapi import Depends

from app.dependency.db import DbSessionDep
from app.repositories.catalog_repository import CatalogRepository
from app.repositories.embedding_cache_repository import EmbeddingCacheRepository


def get_catalog_repository(session: DbSessionDep) -> CatalogRepository:
    return CatalogRepository(session)


def get_embedding_cache_repository(session: DbSessionDep) -> EmbeddingCacheRepository:
    return EmbeddingCacheRepository(session)


CatalogRepositoryDep = Annotated[CatalogRepository, Depends(get_catalog_repository)]
EmbeddingCacheRepositoryDep = Annotated[
    EmbeddingCacheRepository, Depends(get_embedding_cache_repository)
]
