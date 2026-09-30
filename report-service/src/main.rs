use report_service::aws_clients::{build_s3_client, build_sqs_client};
use report_service::consumers::report_generation_consumer::ReportGenerationConsumer;
use report_service::rendering::typst_renderer::TypstRenderer;
use report_service::reporting::context::ReportingContext;
use report_service::repositories::duplicate_repository::DuplicateRepository;
use report_service::repositories::report_document_repository::ReportDocumentRepository;
use report_service::services::request_service::RequestService;
use report_service::services::s3_service::S3Service;
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

    let sqs_client = build_sqs_client(
        &settings.sqs.region,
        settings.sqs.endpoint_url.as_deref(),
        settings.sqs.access_key_id.as_deref(),
        settings.sqs.secret_access_key.as_deref(),
    )
    .await;
    let s3_client = build_s3_client(
        &settings.s3.region,
        settings.s3.endpoint_url.as_deref(),
        settings.s3.access_key_id.as_deref(),
        settings.s3.secret_access_key.as_deref(),
    )
    .await;

    let sqs_service = SqsService::new(sqs_client, settings.sqs.queue_url());
    let s3_service = S3Service::new(s3_client, settings.s3.bucket_name.clone());
    let request_service = RequestService::new(pool.clone());
    let report_document_repository = ReportDocumentRepository::new(pool.clone());
    let reporting_context = ReportingContext {
        duplicate_repository: DuplicateRepository::new(pool),
    };
    let worker_id = format!("report-worker-{}", Uuid::new_v4());
    let consumer = ReportGenerationConsumer::new(
        sqs_service,
        request_service,
        report_document_repository,
        s3_service,
        reporting_context,
        TypstRenderer::new(),
        worker_id,
    );

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
