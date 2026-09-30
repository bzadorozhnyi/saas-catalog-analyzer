import logfire
import openai

from app.core.config import settings


def configure_logfire() -> None:
    # "if-token-present" instead of the default (which errors out when
    # neither a token nor local `logfire auth` credentials are available,
    # e.g. in a container that deliberately doesn't ship either) — falls
    # back to local-only logging instead of crashing the whole process.
    logfire.configure(token=settings.LOGFIRE_TOKEN, send_to_logfire="if-token-present")
    logfire.instrument_pydantic_ai()
    logfire.instrument_openai(openai.AsyncOpenAI)
