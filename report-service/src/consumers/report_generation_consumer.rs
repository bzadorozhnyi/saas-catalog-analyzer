use aws_sdk_sqs::types::Message;
use chrono::Duration as ChronoDuration;
use serde_json::Value;
use std::time::Duration as StdDuration;
use tokio::task::JoinHandle;
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

pub struct ReportGenerationConsumer {
    sqs_service: SqsService,
    request_service: RequestService,
    report_document_repository: ReportDocumentRepository,
    s3_service: S3Service,
    reporting_context: ReportingContext,
    renderer: TypstRenderer,
    worker_id: String,
    lock_duration: ChronoDuration,
    heartbeat_interval: StdDuration,
    visibility_timeout_seconds: i32,
}

/// Aborts the heartbeat task on drop — covers every exit path out of
/// `handle_message` (early return, `?`, panic-unwind) without needing a
/// manual try/finally-style cancel at each one, unlike the Python side's
/// explicit `heartbeat_task.cancel()`.
struct HeartbeatGuard(JoinHandle<()>);

impl Drop for HeartbeatGuard {
    fn drop(&mut self) {
        self.0.abort();
    }
}

/// Bundles everything `heartbeat_loop`/`heartbeat_tick` need, owned by the
/// spawned task — keeps those functions' argument lists from growing every
/// time the heartbeat gains another responsibility.
struct HeartbeatContext {
    request_service: RequestService,
    sqs_service: SqsService,
    request_id: Uuid,
    worker_id: String,
    receipt_handle: String,
    interval: StdDuration,
    lock_duration: ChronoDuration,
    visibility_timeout_seconds: i32,
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
        lock_duration_seconds: i64,
        heartbeat_interval_seconds: i64,
    ) -> Self {
        Self {
            sqs_service,
            request_service,
            report_document_repository,
            s3_service,
            reporting_context,
            renderer,
            worker_id,
            lock_duration: ChronoDuration::seconds(lock_duration_seconds),
            heartbeat_interval: StdDuration::from_secs(
                heartbeat_interval_seconds.max(1).unsigned_abs(),
            ),
            visibility_timeout_seconds: i32::try_from(lock_duration_seconds).unwrap_or(i32::MAX),
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
    /// deleted). Once a request is claimed, `FAILED` is not terminal — SQS's
    /// own redelivery (and eventually its RedrivePolicy/DLQ) drives further
    /// attempts, not a Python/Rust-side counter, so the message is left
    /// alone on a retryable failure rather than deleted. The one exception:
    /// a `ReportingError` we can already prove is permanent (bad
    /// `check_id`, unknown report kind, malformed payload) — retrying can
    /// never help, so we delete the message immediately instead of waiting
    /// out SQS's redelivery cycle for nothing; the request stays `FAILED`
    /// and claimable regardless. The message is left undeleted if we could
    /// not even persist the failure (e.g. Postgres unreachable), mirroring
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
            .claim(request_id, &self.worker_id, self.lock_duration)
            .await?;

        let Some((request, attempt)) = claimed else {
            self.delete_or_log(&receipt_handle).await;
            return Ok(());
        };

        // Keeps the lock alive past `lock_duration` while a slow attempt
        // (e.g. Typst rendering with a cold `@preview` package cache) is
        // still running — dropped (and so aborted) as soon as
        // `execute_attempt` returns, success or failure alike.
        let _heartbeat = self.spawn_heartbeat(request_id, &receipt_handle);

        if let Err(error) = self.execute_attempt(&request, &attempt).await {
            error!(%error, %request_id, "attempt failed");

            let is_permanent = error
                .downcast_ref::<ReportingError>()
                .is_some_and(|error| !error.is_retryable());

            if let Err(fail_error) = self.fail_attempt(&request, &attempt, &error).await {
                error!(%fail_error, %request_id, "could not record failure, leaving for redelivery");
                return Err(fail_error);
            }

            if !is_permanent {
                // Leave the message alone — SQS's own redelivery decides
                // whether this gets another try, not us.
                return Ok(());
            }
            // Known-permanent: no point waiting out SQS's redelivery cycle
            // for something that can never succeed — delete now.
        }

        self.delete_or_log(&receipt_handle).await;
        Ok(())
    }

    /// Spawns a background task that periodically extends both the DB lock
    /// (`RequestService::extend_lock`) and the SQS message's own visibility
    /// timeout (`SqsService::change_message_visibility`), stopping itself
    /// only once the DB lock is definitively lost. Mirrors
    /// `CatalogCreationConsumer._heartbeat` on the Python side.
    fn spawn_heartbeat(&self, request_id: Uuid, receipt_handle: &str) -> HeartbeatGuard {
        let context = HeartbeatContext {
            request_service: self.request_service.clone(),
            sqs_service: self.sqs_service.clone(),
            request_id,
            worker_id: self.worker_id.clone(),
            receipt_handle: receipt_handle.to_string(),
            interval: self.heartbeat_interval,
            lock_duration: self.lock_duration,
            visibility_timeout_seconds: self.visibility_timeout_seconds,
        };

        HeartbeatGuard(tokio::spawn(Self::heartbeat_loop(context)))
    }

    /// Runs until `heartbeat_tick` reports the DB lock is already lost. A
    /// free-standing `async fn` (rather than an inline closure body) so the
    /// loop isn't nested inside both `tokio::spawn`'s closure and
    /// `spawn_heartbeat` itself.
    async fn heartbeat_loop(context: HeartbeatContext) {
        loop {
            tokio::time::sleep(context.interval).await;
            if !Self::heartbeat_tick(&context).await {
                return;
            }
        }
    }

    /// Extends the DB lock and, independently, the SQS visibility timeout.
    /// The two are unrelated systems (mirrors the "no coordinated writes
    /// across two systems" rule behind the DLQ redrive design) — a failure
    /// in either alone is treated as transient and just logged, since the
    /// other still protects against a concurrent claim/redelivery, and a
    /// missed tick self-heals on the next one thanks to
    /// `lock_duration`/`heartbeat_interval`'s safety margin. The one signal
    /// that DOES stop the loop is the DB's `Ok(false)`: an authoritative
    /// "you no longer hold this row" (via `WHERE locked_by = worker_id`),
    /// unlike an `Err` from either call, which only means "could not check
    /// right now." If the lock is genuinely gone there's also no point
    /// fighting to keep the SQS message hidden for a claim we no longer
    /// have, so that call is skipped in this branch.
    async fn heartbeat_tick(context: &HeartbeatContext) -> bool {
        match context
            .request_service
            .extend_lock(
                context.request_id,
                &context.worker_id,
                context.lock_duration,
            )
            .await
        {
            Ok(true) => {}
            Ok(false) => {
                warn!(request_id = %context.request_id, "heartbeat: lock already lost, stopping");
                return false;
            }
            Err(error) => {
                error!(%error, request_id = %context.request_id, "heartbeat failed to extend DB lock, will retry");
            }
        }

        if let Err(error) = context
            .sqs_service
            .change_message_visibility(&context.receipt_handle, context.visibility_timeout_seconds)
            .await
        {
            error!(%error, request_id = %context.request_id, "heartbeat failed to extend SQS visibility timeout, will retry");
        }

        true
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

        let blob_name = format!("{report_kind}/{report_version}/{}.pdf", attempt.id);
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

    /// Records a failed attempt. Mirrors
    /// `CatalogCreationWorkerService._handle_failure` on the Python side.
    /// Returns `Err` only if recording the failure itself failed.
    async fn fail_attempt(
        &self,
        request: &Request,
        attempt: &RequestAttempt,
        error: &anyhow::Error,
    ) -> anyhow::Result<()> {
        self.request_service
            .fail(request.id, &self.worker_id, attempt.id, &error.to_string())
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
