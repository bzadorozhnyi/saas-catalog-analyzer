from app.ai.agents import classification_agent
from app.ai.schemas import ClassificationResult


class ClassificationService:
    async def classify(self, name: str, description: str) -> ClassificationResult:
        prompt = f"Name: {name}\nDescription: {description}"
        run_result = await classification_agent.run(prompt)
        return run_result.output
