import time

from app.ai.agents import explain_duplicate_agent
from app.ai.schemas import ExplainDuplicateResult
from app.core.config import settings
from app.core.llm_call_batcher import log_llm_call
from app.enums.llm_call_purpose_enum import LlmCallPurposeEnum
from app.enums.llm_call_status_enum import LlmCallStatusEnum
from app.repositories.catalog_repository import CatalogRepository


class DuplicateExplanationService:
    def __init__(self, repository: CatalogRepository) -> None:
        self._repository = repository

    async def explain(self, name_a: str, name_b: str) -> ExplainDuplicateResult:
        prompt = (
            f"Are '{name_a}' and '{name_b}' duplicate SaaS subscriptions? "
            "Look up both in the catalog before answering."
        )
        started_at = time.monotonic()
        try:
            run_result = await explain_duplicate_agent.run(prompt, deps=self._repository)
        except Exception:
            log_llm_call(
                purpose=LlmCallPurposeEnum.EXPLAIN_DUPLICATE,
                model=settings.AI.CLASSIFICATION_MODEL,
                input_tokens=0,
                output_tokens=None,
                latency_ms=int((time.monotonic() - started_at) * 1000),
                status=LlmCallStatusEnum.ERROR,
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
        )
        return run_result.output
