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


def current_trace_id() -> str | None:
    """The W3C trace ID of the currently active span, if any.

    `logfire.get_context()` returns a carrier dict with a `traceparent`
    header formatted as `00-<trace_id>-<span_id>-<flags>`; the trace ID is
    the stable 32-hex-char segment that identifies the whole trace, as
    opposed to the span ID, which changes per span. Used purely as a
    correlation string across process boundaries for now (API -> dispatcher
    -> SQS -> worker/report-service) — nothing yet re-attaches it as a
    parent span, so no actual span linking happens across those boundaries.
    """
    traceparent = logfire.get_context().get("traceparent")
    if traceparent is None:
        return None
    return traceparent.split("-")[1]
