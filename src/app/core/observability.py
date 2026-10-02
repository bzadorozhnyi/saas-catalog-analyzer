import logfire
import openai
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from app.core.config import settings


def configure_logfire() -> None:
    # Logfire is an ergonomic API over the standard `opentelemetry-sdk` —
    # `additional_span_processors` attaches an extra exporter to the same
    # `TracerProvider` it builds, so every span created anywhere (including
    # Logfire's own auto-instrumentation below) also flows to our
    # self-hosted collector. `OTLPSpanExporter()` with no args reads the
    # standard `OTEL_EXPORTER_OTLP_ENDPOINT` env var itself. Unset = no
    # self-hosted export, same as before.
    additional_span_processors = (
        [BatchSpanProcessor(OTLPSpanExporter())]
        if settings.OTEL_EXPORTER_OTLP_ENDPOINT is not None
        else None
    )

    # "if-token-present" instead of the default (which errors out when
    # neither a token nor local `logfire auth` credentials are available,
    # e.g. in a container that deliberately doesn't ship either) — falls
    # back to local-only logging instead of crashing the whole process.
    logfire.configure(
        token=settings.LOGFIRE_TOKEN,
        send_to_logfire="if-token-present",
        additional_span_processors=additional_span_processors,
    )
    logfire.instrument_pydantic_ai()
    logfire.instrument_openai(openai.AsyncOpenAI)


def current_trace_context() -> str | None:
    """The full W3C `traceparent` header of the currently active span, if
    any — `00-<trace_id>-<span_id>-<flags>`. Pass this to
    `logfire.attach_context()` (via `parse_trace_context()`) in a consumer
    to make a new span a real child of the span active when this was
    captured, even across a process boundary (API -> dispatcher -> SQS ->
    worker/report-service).
    """
    return logfire.get_context().get("traceparent")


def parse_trace_context(trace_context: str | None) -> dict[str, str]:
    """The inverse of capturing with `current_trace_context()` — rebuilds
    the carrier dict `logfire.attach_context()` expects from a stored
    `traceparent` string. Returns an empty dict (attach a no-op/empty
    context) if there's nothing to restore.
    """
    return {"traceparent": trace_context} if trace_context else {}


def current_trace_id() -> str | None:
    """The W3C trace ID of the currently active span, if any — just the
    stable 32-hex-char segment of the traceparent that identifies the whole
    trace, dropping the span ID. Enough for human/DB correlation (grep or
    query everything tagged with one request's trace_id) but NOT enough to
    re-attach a span as a child — see `current_trace_context()` for that.
    """
    traceparent = logfire.get_context().get("traceparent")
    if traceparent is None:
        return None
    return traceparent.split("-")[1]
