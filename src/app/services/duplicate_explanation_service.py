import time
import uuid

import logfire
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.agents import explain_duplicate_agent
from app.ai.schemas import ExplainDuplicateResult
from app.core.config import settings
from app.core.exceptions import NotFoundException
from app.core.llm_call_batcher import log_llm_call
from app.core.observability import current_trace_id
from app.enums.llm_call_purpose_enum import LlmCallPurposeEnum
from app.enums.llm_call_status_enum import LlmCallStatusEnum
from app.repositories.catalog_repository import CatalogRepository
from app.repositories.duplicate_repository import DuplicateRepository


class DuplicateExplanationService:
    def __init__(
        self,
        session: AsyncSession,
        catalog_repository: CatalogRepository,
        duplicate_repository: DuplicateRepository,
    ) -> None:
        self._session = session
        self._catalog_repository = catalog_repository
        self._duplicate_repository = duplicate_repository

    async def explain(self, pair_id: uuid.UUID) -> ExplainDuplicateResult:
        pair = await self._duplicate_repository.get(pair_id)
        if pair is None:
            raise NotFoundException(msg=f"Duplicate pair {pair_id} not found")

        prompt = (
            f"Are '{pair.name_a}' and '{pair.name_b}' duplicate SaaS subscriptions? "
            "Look up both in the catalog before answering."
        )
        trace_id = current_trace_id()
        started_at = time.monotonic()
        try:
            run_result = await explain_duplicate_agent.run(prompt, deps=self._catalog_repository)
        except Exception:
            log_llm_call(
                purpose=LlmCallPurposeEnum.EXPLAIN_DUPLICATE,
                model=settings.AI.CLASSIFICATION_MODEL,
                input_tokens=0,
                output_tokens=None,
                latency_ms=int((time.monotonic() - started_at) * 1000),
                status=LlmCallStatusEnum.ERROR,
                trace_id=trace_id,
            )
            raise

        usage = run_result.usage
        log_llm_call(
            purpose=LlmCallPurposeEnum.EXPLAIN_DUPLICATE,
            model=settings.AI.CLASSIFICATION_MODEL,
            input_tokens=usage.input_tokens,
            output_tokens=usage.output_tokens,
            latency_ms=int((time.monotonic() - started_at) * 1000),
            status=LlmCallStatusEnum.SUCCESS,
            trace_id=trace_id,
        )

        result = run_result.output
        await self._duplicate_repository.update_explanation(
            pair_id,
            result.is_duplicate,
            result.confidence,
            result.reasoning,
            result.overlapping_features,
        )
        try:
            await self._session.commit()
        except Exception:
            logfire.exception("Failed to commit explanation for pair {pair_id}", pair_id=pair_id)
            await self._session.rollback()
            raise

        return result
