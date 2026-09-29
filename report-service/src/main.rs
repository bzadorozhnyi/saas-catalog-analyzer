use aws_config::Region;
use aws_sdk_sqs::config::Credentials;
use report_service::consumers::report_generation_consumer::ReportGenerationConsumer;
use report_service::rendering::typst_renderer::TypstRenderer;
use report_service::reporting::context::ReportingContext;
use report_service::reporting::registry::build_report;
use report_service::repositories::duplicate_repository::DuplicateRepository;
use report_service::repositories::request_repository::RequestRepository;
use report_service::services::request_service::RequestService;
use report_service::services::sqs_service::SqsService;
use report_service::settings::Settings;
use tracing::{error, info};
use uuid::Uuid;

const MAX_MESSAGES: i32 = 5;
const WAIT_SECONDS: i32 = 20;

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    tracing_subscriber::fmt()
        .with_env_filter(tracing_subscriber::EnvFilter::from_default_env())
        .init();

    let settings = Settings::load()?;

    let pool = sqlx::postgres::PgPoolOptions::new()
        .max_connections(5)
        .connect(&settings.db.url())
        .await?;

    if let Ok(check_id) = std::env::var("SMOKE_TEST_CHECK_ID") {
        reporting_smoke_test(pool.clone(), check_id.parse()?).await?;
    }

    let mut aws_config_loader = aws_config::defaults(aws_config::BehaviorVersion::latest())
        .region(Region::new(settings.sqs.region.clone()));
    if let Some(endpoint_url) = &settings.sqs.endpoint_url {
        let access_key = settings.sqs.access_key_id.as_deref().unwrap_or("test");
        let secret_key = settings.sqs.secret_access_key.as_deref().unwrap_or("test");
        aws_config_loader = aws_config_loader
            .endpoint_url(endpoint_url)
            .credentials_provider(Credentials::new(
                access_key, secret_key, None, None, "static",
            ));
    }
    let aws_config = aws_config_loader.load().await;
    let sqs_client = aws_sdk_sqs::Client::new(&aws_config);

    let sqs_service = SqsService::new(sqs_client, settings.sqs.queue_url());
    let request_service = RequestService::new(RequestRepository::new(pool));
    let worker_id = format!("report-worker-{}", Uuid::new_v4());
    let consumer = ReportGenerationConsumer::new(sqs_service, request_service, worker_id);

    info!(
        queue_url = settings.sqs.queue_url(),
        "report-service started"
    );

    loop {
        if let Err(error) = consumer.run_once(MAX_MESSAGES, WAIT_SECONDS).await {
            error!(%error, "failed to receive messages from SQS");
        }
    }
}

/// Temporary: exercises the full pipeline (repository -> `build_report` ->
/// Typst render -> PDF bytes) against a real, already-persisted
/// `duplicate_checks`/`duplicate_pairs` row. Only runs when
/// `SMOKE_TEST_CHECK_ID` is set. Will be removed once this is wired into the
/// consumer for real.
async fn reporting_smoke_test(pool: sqlx::PgPool, check_id: Uuid) -> anyhow::Result<()> {
    let context = ReportingContext {
        duplicate_repository: DuplicateRepository::new(pool),
    };
    let render_request = build_report(&context, "duplicate_detection", "v1", check_id).await?;

    let template_path = format!("templates/{}", render_request.template_path);
    let template_text = std::fs::read_to_string(&template_path)?;

    let renderer = TypstRenderer::new();
    let pdf_bytes = renderer.render(template_text, render_request.data_json)?;

    let is_pdf = pdf_bytes.starts_with(b"%PDF");
    info!(bytes = pdf_bytes.len(), is_pdf, "reporting smoke test");
    anyhow::ensure!(is_pdf, "output does not look like a PDF");

    std::fs::write("/tmp/duplicate_report_v1_smoke_test.pdf", &pdf_bytes)?;
    Ok(())
}
