import time

from app.ai.agents import classification_agent
from app.ai.schemas import ClassificationResult
from app.core.config import settings
from app.core.llm_call_batcher import log_llm_call
from app.enums.llm_call_purpose_enum import LlmCallPurposeEnum
from app.enums.llm_call_status_enum import LlmCallStatusEnum


class ClassificationService:
    async def classify(self, name: str, description: str) -> ClassificationResult:
        prompt = f"Name: {name}\nDescription: {description}"
        started_at = time.monotonic()
        try:
            run_result = await classification_agent.run(prompt)
        except Exception:
            log_llm_call(
                purpose=LlmCallPurposeEnum.CLASSIFICATION,
                model=settings.AI.CLASSIFICATION_MODEL,
                input_tokens=0,
                output_tokens=None,
                latency_ms=int((time.monotonic() - started_at) * 1000),
                status=LlmCallStatusEnum.ERROR,
            )
            raise

        usage = run_result.usage
        log_llm_call(
            purpose=LlmCallPurposeEnum.CLASSIFICATION,
            model=settings.AI.CLASSIFICATION_MODEL,
            input_tokens=usage.input_tokens,
            output_tokens=usage.output_tokens,
            latency_ms=int((time.monotonic() - started_at) * 1000),
            status=LlmCallStatusEnum.SUCCESS,
        )
        return run_result.output
