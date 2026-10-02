use std::collections::HashMap;

use opentelemetry::Context as OtelContext;
use opentelemetry::propagation::TextMapPropagator;
use opentelemetry::trace::TracerProvider as _;
use opentelemetry_otlp::SpanExporter;
use opentelemetry_sdk::Resource;
use opentelemetry_sdk::propagation::TraceContextPropagator;
use opentelemetry_sdk::runtime::Tokio;
use opentelemetry_sdk::trace::SdkTracerProvider;
use opentelemetry_sdk::trace::span_processor_with_async_runtime::BatchSpanProcessor;
use tracing_subscriber::EnvFilter;
use tracing_subscriber::layer::SubscriberExt;
use tracing_subscriber::util::SubscriberInitExt;

const SERVICE_NAME: &str = "report-service";

/// Sets up `tracing_subscriber` with console output (as before) plus, when
/// `otlp_endpoint` is configured, an additional layer that exports spans to
/// a self-hosted OTLP collector (e.g. Jaeger) — mirrors the Python side's
/// `configure_logfire()` / `additional_span_processors`. Unset endpoint =
/// unchanged console-only behavior.
pub fn init_tracing(otlp_endpoint: Option<&str>) -> anyhow::Result<()> {
    let fmt_layer = tracing_subscriber::fmt::layer();
    let env_filter = EnvFilter::from_default_env();

    if otlp_endpoint.is_none() {
        tracing_subscriber::registry()
            .with(env_filter)
            .with(fmt_layer)
            .init();
        return Ok(());
    }

    // `otlp_endpoint` above is only the on/off gate — deliberately NOT
    // passed into `.with_endpoint()`. That method takes the value verbatim
    // with no `/v1/traces` suffixing (unlike the OTEL_EXPORTER_OTLP_ENDPOINT
    // env var path, which does append it), so calling it with our bare
    // "http://jaeger:4318" 404s. Letting the exporter read the env var
    // itself takes the path that adds the suffix correctly.
    let exporter = SpanExporter::builder().with_http().build()?;

    let processor = BatchSpanProcessor::builder(exporter, Tokio).build();

    let provider = SdkTracerProvider::builder()
        .with_span_processor(processor)
        .with_resource(Resource::builder().with_service_name(SERVICE_NAME).build())
        .build();

    let tracer = provider.tracer(SERVICE_NAME);
    opentelemetry::global::set_tracer_provider(provider);

    let otel_layer = tracing_opentelemetry::layer().with_tracer(tracer);

    tracing_subscriber::registry()
        .with(env_filter)
        .with(fmt_layer)
        .with(otel_layer)
        .init();

    Ok(())
}

/// Rebuilds the remote parent context from a stored W3C `traceparent`
/// string, for `tracing::Span::set_parent()`. Mirrors the Python side's
/// `parse_trace_context()` / `logfire.attach_context()`. An absent
/// `trace_context` yields an empty context — the new span just starts its
/// own trace instead of erroring.
#[must_use]
pub fn remote_parent_context(trace_context: Option<&str>) -> OtelContext {
    let Some(traceparent) = trace_context else {
        return OtelContext::new();
    };
    let mut carrier = HashMap::new();
    carrier.insert("traceparent".to_string(), traceparent.to_string());
    TraceContextPropagator::new().extract(&carrier)
}
