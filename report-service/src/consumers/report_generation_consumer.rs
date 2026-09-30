use aws_sdk_sqs::types::Message;
use chrono::Duration;
use serde_json::Value;
use tracing::{error, info, warn};
use uuid::Uuid;

use crate::dto::request::Request;
use crate::dto::request_attempt::RequestAttempt;
use crate::enums::content_type_enum::ContentType;
use crate::errors::reporting_error::ReportingError;
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
    max_attempts: i32,
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
        max_attempts: i32,
    ) -> Self {
        Self {
            sqs_service,
            request_service,
            report_document_repository,
            s3_service,
            reporting_context,
            renderer,
            worker_id,
            max_attempts,
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
    /// deleted). Once a request is claimed, retries are driven entirely by
    /// `requests.status` (`PENDING` picked up again by the dispatcher, or
    /// `FAILED` for good) — not by SQS's own redelivery — so the message is
    /// deleted after every recorded outcome, success or failure alike. The
    /// message is left undeleted only if we could not even persist the
    /// failure (e.g. Postgres unreachable), mirroring
    /// `CatalogCreationConsumer._handle_message` /
    /// `CatalogCreationWorkerService.process` on the Python side. Unlike
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

        let Some((request, attempt)) = claimed else {
            self.delete_or_log(&receipt_handle).await;
            return Ok(());
        };

        if let Err(error) = self.execute_attempt(&request, &attempt).await {
            error!(%error, %request_id, "attempt failed");
            if let Err(fail_error) = self.fail_attempt(&request, &attempt, &error).await {
                error!(%fail_error, %request_id, "could not record failure, leaving for redelivery");
                return Err(fail_error);
            }
        }

        self.delete_or_log(&receipt_handle).await;
        Ok(())
    }

    /// Runs the full happy path: parse payload, build + render the report,
    /// upload it, and mark the request completed. Mirrors
    /// `CatalogCreationWorkerService._execute_attempt` on the Python side.
    async fn execute_attempt(
        &self,
        request: &Request,
        attempt: &RequestAttempt,
    ) -> anyhow::Result<()> {
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

        let blob_name = format!("{report_kind}/{report_version}/{}.pdf", request.id);
        self.s3_service
            .upload(&blob_name, pdf_bytes, ContentType::Pdf)
            .await?;
        let report_document = self
            .report_document_repository
            .create(request.id, &blob_name)
            .await?;

        let success_message = format!("generated report document {}", report_document.id);
        let completed = self
            .request_service
            .complete(
                request.id,
                &self.worker_id,
                attempt.id,
                Some(report_document.id),
                &success_message,
            )
            .await?;
        if completed {
            info!(request_id = %request.id, "report request completed");
        } else {
            // Another worker already took over — nothing left for us to do.
            warn!(request_id = %request.id, "lost claim on request, another worker took over");
        }
        Ok(())
    }

    /// Classifies a failed attempt — permanent (via `ReportingError`) or
    /// attempts-exhausted means `FAILED` for good; otherwise back to
    /// `PENDING` for the dispatcher to retry. Mirrors
    /// `CatalogCreationWorkerService._handle_failure` on the Python side.
    /// Returns `Err` only if recording the failure itself failed.
    async fn fail_attempt(
        &self,
        request: &Request,
        attempt: &RequestAttempt,
        error: &anyhow::Error,
    ) -> anyhow::Result<()> {
        let is_permanent = error
            .downcast_ref::<ReportingError>()
            .is_some_and(|error| !error.is_retryable());
        let is_terminal = is_permanent || attempt.attempt_number >= self.max_attempts;

        self.request_service
            .fail(
                request.id,
                &self.worker_id,
                attempt.id,
                &error.to_string(),
                is_terminal,
            )
            .await?;
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
    fn parse_report_payload(payload: &Value) -> Result<(String, String, Uuid), ReportingError> {
        let report_kind = payload
            .get("report_kind")
            .and_then(Value::as_str)
            .ok_or_else(|| ReportingError::InvalidPayload("missing report_kind".to_string()))?
            .to_string();
        let report_version = payload
            .get("report_version")
            .and_then(Value::as_str)
            .ok_or_else(|| ReportingError::InvalidPayload("missing report_version".to_string()))?
            .to_string();
        let check_id_str = payload
            .get("check_id")
            .and_then(Value::as_str)
            .ok_or_else(|| ReportingError::InvalidPayload("missing check_id".to_string()))?;
        let check_id = Uuid::parse_str(check_id_str)
            .map_err(|error| ReportingError::InvalidPayload(error.to_string()))?;
        Ok((report_kind, report_version, check_id))
    }
}
