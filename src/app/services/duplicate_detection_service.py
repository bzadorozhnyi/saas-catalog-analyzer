import logfire
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.response import DuplicatePairResponse
from app.core.exceptions import NotFoundException
from app.enums.duplicate_verdict_enum import DuplicateVerdictEnum
from app.repositories.catalog_repository import CatalogRepository
from app.repositories.duplicate_repository import DuplicateRepository


class DuplicateDetectionService:
    def __init__(
        self,
        session: AsyncSession,
        catalog_repository: CatalogRepository,
        duplicate_repository: DuplicateRepository,
    ) -> None:
        self._session = session
        self._catalog_repository = catalog_repository
        self._duplicate_repository = duplicate_repository

    async def find_duplicates(
        self,
        subscription_names: list[str],
        duplicate_threshold: float,
        review_threshold: float,
    ) -> list[DuplicatePairResponse]:
        known_items = await self._catalog_repository.list_by_names(subscription_names)
        known_names = {item.name for item in known_items}
        unknown_names = set(subscription_names) - known_names
        if unknown_names:
            raise NotFoundException(
                msg="Unknown subscription names", details=sorted(unknown_names)
            )

        pairs = await self._catalog_repository.find_similar_pairs(
            subscription_names, review_threshold
        )

        check = await self._duplicate_repository.create_check(
            subscription_names, duplicate_threshold, review_threshold
        )
        entries = [
            (
                pair.name_a,
                pair.name_b,
                pair.similarity,
                DuplicateVerdictEnum.LIKELY_DUPLICATE
                if pair.similarity > duplicate_threshold
                else DuplicateVerdictEnum.REVIEW_MANUALLY,
            )
            for pair in pairs
        ]
        persisted_pairs = await self._duplicate_repository.create_pairs(check.id, entries)
        try:
            await self._session.commit()
        except Exception:
            logfire.exception("Failed to commit duplicate check {check_id}", check_id=check.id)
            await self._session.rollback()
            raise

        return [
            DuplicatePairResponse(
                id=pair.id,
                name_a=pair.name_a,
                name_b=pair.name_b,
                similarity=pair.similarity,
                verdict="likely_duplicate"
                if pair.verdict == DuplicateVerdictEnum.LIKELY_DUPLICATE
                else "review_manually",
            )
            for pair in persisted_pairs
        ]
