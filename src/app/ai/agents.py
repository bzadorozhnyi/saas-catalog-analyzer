from pydantic_ai import Agent, ModelRetry, RunContext
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

from app.ai.prompts import CLASSIFICATION_SYSTEM_PROMPT
from app.ai.schemas import ClassificationResult
from app.core.config import settings

classification_model = OpenAIChatModel(
    settings.classification_model,
    provider=OpenAIProvider(api_key=settings.openai_api_key),
)

classification_agent: Agent[None, ClassificationResult] = Agent(
    classification_model,
    output_type=ClassificationResult,
    system_prompt=CLASSIFICATION_SYSTEM_PROMPT,
)


@classification_agent.output_validator
def validate_reasoning(ctx: RunContext[None], result: ClassificationResult) -> ClassificationResult:
    if not result.reasoning.strip():
        raise ModelRetry("reasoning must not be empty — explain why you picked this category.")
    return result
