import logfire
import openai

from app.core.config import settings


def configure_logfire() -> None:
    logfire.configure(token=settings.LOGFIRE_TOKEN)
    logfire.instrument_pydantic_ai()
    logfire.instrument_openai(openai.AsyncOpenAI)
