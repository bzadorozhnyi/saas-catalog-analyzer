use aws_sdk_sqs::types::Message;
use chrono::Duration;
use serde_json::Value;
use tracing::{error, info};
use uuid::Uuid;

use crate::enums::content_type_enum::ContentType;
use crate::rendering::typst_renderer::TypstRenderer;
use crate::reporting::context::ReportingContext;
use crate::reporting::registry::build_report;
use crate::repositories::report_document_repository::ReportDocumentRepository;
use crate::services::request_service::RequestService;
use crate::services::s3_service::S3Service;
use crate::services::sqs_service::SqsService;

const LOCK_DURATION_SECONDS: i64 = 60;

pub struct ReportGenerationConsumer {
    sqs_service: SqsService,
    request_service: RequestService,
    report_document_repository: ReportDocumentRepository,
    s3_service: S3Service,
    reporting_context: ReportingContext,
    renderer: TypstRenderer,
    worker_id: String,
}

impl ReportGenerationConsumer {
    #[must_use]
    #[allow(clippy::too_many_arguments)]
    pub fn new(
        sqs_service: SqsService,
        request_service: RequestService,
        report_document_repository: ReportDocumentRepository,
        s3_service: S3Service,
        reporting_context: ReportingContext,
        renderer: TypstRenderer,
        worker_id: String,
    ) -> Self {
        Self {
            sqs_service,
            request_service,
            report_document_repository,
            s3_service,
            reporting_context,
            renderer,
            worker_id,
        }
    }

    pub async fn run_once(&self, max_messages: i32, wait_seconds: i32) -> anyhow::Result<()> {
        let messages = self
            .sqs_service
            .receive_messages(max_messages, wait_seconds)
            .await?;
        for message in messages {
            if let Err(error) = self.handle_message(message).await {
                error!(%error, "failed to handle SQS message");
            }
        }
        Ok(())
    }

    /// Malformed bodies and lost claims are handled here (logged, message
    /// deleted). A `claim()` failure (e.g. Postgres unreachable) and any
    /// failure while building/rendering/storing the report propagate instead
    /// — the message is left undeleted for SQS redelivery (eventually
    /// landing in the DLQ after `maxReceiveCount`), mirroring
    /// `CatalogCreationConsumer._handle_message` on the Python side. Unlike
    /// Python's `asyncio.gather`-based batch (which cancels sibling messages
    /// on the first error), messages here are handled one at a time, so a
    /// failure on one does not abort the rest of the batch.
    async fn handle_message(&self, message: Message) -> anyhow::Result<()> {
        let Some(receipt_handle) = message.receipt_handle.clone() else {
            error!("SQS message missing receipt handle, skipping");
            return Ok(());
        };

        let request_id = match Self::parse_request_id(&message) {
            Ok(id) => id,
            Err(error) => {
                error!(%error, "malformed SQS message, deleting");
                self.delete_or_log(&receipt_handle).await;
                return Ok(());
            }
        };

        let claimed = self
            .request_service
            .claim(
                request_id,
                &self.worker_id,
                Duration::seconds(LOCK_DURATION_SECONDS),
            )
            .await?;

        let Some(request) = claimed else {
            self.delete_or_log(&receipt_handle).await;
            return Ok(());
        };

        let (report_kind, report_version, check_id) = Self::parse_report_payload(&request.payload)?;

        let render_request = build_report(
            &self.reporting_context,
            &report_kind,
            &report_version,
            check_id,
        )
        .await?;
        let template_text =
            std::fs::read_to_string(format!("templates/{}", render_request.template_path))?;
        let pdf_bytes = self
            .renderer
            .render(template_text, render_request.data_json)?;

        let blob_name = format!("{report_kind}/{report_version}/{request_id}.pdf");
        self.s3_service
            .upload(&blob_name, pdf_bytes, ContentType::Pdf)
            .await?;
        let report_document = self
            .report_document_repository
            .create(request_id, &blob_name)
            .await?;

        match self
            .request_service
            .complete(request_id, &self.worker_id, Some(report_document.id))
            .await
        {
            Ok(true) => info!(%request_id, "report request completed"),
            Ok(false) => error!(%request_id, "complete() lost the lock before finishing"),
            Err(error) => error!(%error, %request_id, "complete() failed"),
        }

        self.delete_or_log(&receipt_handle).await;
        Ok(())
    }

    async fn delete_or_log(&self, receipt_handle: &str) {
        if let Err(error) = self.sqs_service.delete_message(receipt_handle).await {
            error!(%error, "failed to delete SQS message");
        }
    }

    fn parse_request_id(message: &Message) -> anyhow::Result<Uuid> {
        let body = message
            .body
            .as_deref()
            .ok_or_else(|| anyhow::anyhow!("message has no body"))?;
        let json: Value = serde_json::from_str(body)?;
        let request_id_str = json
            .get("request_id")
            .and_then(Value::as_str)
            .ok_or_else(|| anyhow::anyhow!("missing request_id"))?;
        Ok(Uuid::parse_str(request_id_str)?)
    }

    /// Parses the `GENERATE_REPORT` request payload built by
    /// `GenerateReportUseCase` on the Python side: `{report_kind,
    /// report_version, check_id}`.
    fn parse_report_payload(payload: &Value) -> anyhow::Result<(String, String, Uuid)> {
        let report_kind = payload
            .get("report_kind")
            .and_then(Value::as_str)
            .ok_or_else(|| anyhow::anyhow!("payload missing report_kind"))?
            .to_string();
        let report_version = payload
            .get("report_version")
            .and_then(Value::as_str)
            .ok_or_else(|| anyhow::anyhow!("payload missing report_version"))?
            .to_string();
        let check_id_str = payload
            .get("check_id")
            .and_then(Value::as_str)
            .ok_or_else(|| anyhow::anyhow!("payload missing check_id"))?;
        let check_id = Uuid::parse_str(check_id_str)?;
        Ok((report_kind, report_version, check_id))
    }
}
