from pydantic_ai import Agent, ModelRetry, RunContext
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

from app.ai.prompts import CLASSIFICATION_SYSTEM_PROMPT, EXPLAIN_DUPLICATE_SYSTEM_PROMPT
from app.ai.schemas import ClassificationResult, ExplainDuplicateResult
from app.core.config import settings
from app.repositories.catalog_repository import CatalogRepository

classification_model = OpenAIChatModel(
    settings.AI.CLASSIFICATION_MODEL,
    provider=OpenAIProvider(api_key=settings.AI.OPENAI_API_KEY),
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


explain_duplicate_agent: Agent[CatalogRepository, ExplainDuplicateResult] = Agent(
    classification_model,
    deps_type=CatalogRepository,
    output_type=ExplainDuplicateResult,
    system_prompt=EXPLAIN_DUPLICATE_SYSTEM_PROMPT,
)


@explain_duplicate_agent.tool
async def get_software_details(ctx: RunContext[CatalogRepository], name: str) -> str:
    item = await ctx.deps.get_by_name(name)
    if item is None:
        return f"No software named '{name}' was found in the catalog."
    return f"Name: {item.name}\nCategory: {item.category}\nDescription: {item.description}"
