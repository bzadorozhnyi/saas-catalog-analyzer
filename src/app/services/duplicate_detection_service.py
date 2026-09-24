from app.api.v1.schemas.response import DuplicatePairResponse
from app.core.exceptions import NotFoundException
from app.repositories.catalog_repository import CatalogRepository


class DuplicateDetectionService:
    def __init__(self, repository: CatalogRepository) -> None:
        self._repository = repository

    async def find_duplicates(
        self,
        subscription_names: list[str],
        duplicate_threshold: float,
        review_threshold: float,
    ) -> list[DuplicatePairResponse]:
        known_items = await self._repository.list_by_names(subscription_names)
        known_names = {item.name for item in known_items}
        unknown_names = set(subscription_names) - known_names
        if unknown_names:
            raise NotFoundException(
                msg="Unknown subscription names", details=sorted(unknown_names)
            )

        pairs = await self._repository.find_similar_pairs(subscription_names, review_threshold)
        return [
            DuplicatePairResponse(
                name_a=pair.name_a,
                name_b=pair.name_b,
                similarity=pair.similarity,
                verdict="likely_duplicate"
                if pair.similarity > duplicate_threshold
                else "review_manually",
            )
            for pair in pairs
        ]
