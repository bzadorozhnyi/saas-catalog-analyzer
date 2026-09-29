import uuid
from typing import cast

from sqlalchemy import CursorResult, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func

from app.enums.duplicate_verdict_enum import DuplicateVerdictEnum
from app.models.duplicate_check import DuplicateCheck
from app.models.duplicate_pair import DuplicatePair


class DuplicateRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_check(
        self, subscription_names: list[str], duplicate_threshold: float, review_threshold: float
    ) -> DuplicateCheck:
        check = DuplicateCheck(
            subscription_names=subscription_names,
            duplicate_threshold=duplicate_threshold,
            review_threshold=review_threshold,
        )
        self._session.add(check)
        await self._session.flush()
        return check

    async def create_pairs(
        self,
        check_id: uuid.UUID,
        entries: list[tuple[str, str, float, DuplicateVerdictEnum]],
    ) -> list[DuplicatePair]:
        pairs = [
            DuplicatePair(
                check_id=check_id,
                name_a=name_a,
                name_b=name_b,
                similarity=similarity,
                verdict=verdict,
            )
            for name_a, name_b, similarity, verdict in entries
        ]
        self._session.add_all(pairs)
        await self._session.flush()
        return pairs

    async def get(self, pair_id: uuid.UUID) -> DuplicatePair | None:
        return await self._session.get(DuplicatePair, pair_id)

    async def update_explanation(
        self,
        pair_id: uuid.UUID,
        is_duplicate: bool,
        confidence: float,
        reasoning: str,
        overlapping_features: list[str],
    ) -> bool:
        stmt = (
            update(DuplicatePair)
            .where(DuplicatePair.id == pair_id)
            .values(
                is_duplicate=is_duplicate,
                confidence=confidence,
                reasoning=reasoning,
                overlapping_features=overlapping_features,
                explained_at=func.now(),
            )
        )
        result = cast(CursorResult, await self._session.execute(stmt))
        return result.rowcount == 1
