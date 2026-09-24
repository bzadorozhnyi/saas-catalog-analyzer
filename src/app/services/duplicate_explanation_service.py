from app.ai.agents import explain_duplicate_agent
from app.ai.schemas import ExplainDuplicateResult
from app.repositories.catalog_repository import CatalogRepository


class DuplicateExplanationService:
    def __init__(self, repository: CatalogRepository) -> None:
        self._repository = repository

    async def explain(self, name_a: str, name_b: str) -> ExplainDuplicateResult:
        prompt = (
            f"Are '{name_a}' and '{name_b}' duplicate SaaS subscriptions? "
            "Look up both in the catalog before answering."
        )
        run_result = await explain_duplicate_agent.run(prompt, deps=self._repository)
        return run_result.output
