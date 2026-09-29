use aws_sdk_sqs::types::Message;
use chrono::Duration;
use serde_json::Value;
use tracing::{error, info};
use uuid::Uuid;

use crate::services::request_service::RequestService;
use crate::services::sqs_service::SqsService;

const LOCK_DURATION_SECONDS: i64 = 60;

pub struct ReportGenerationConsumer {
    sqs_service: SqsService,
    request_service: RequestService,
    worker_id: String,
}

impl ReportGenerationConsumer {
    #[must_use]
    pub fn new(
        sqs_service: SqsService,
        request_service: RequestService,
        worker_id: String,
    ) -> Self {
        Self {
            sqs_service,
            request_service,
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
    /// deleted). A `claim()` failure (e.g. Postgres unreachable) propagates
    /// instead — the message is left undeleted for SQS redelivery, mirroring
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

        let Some(_request) = claimed else {
            self.delete_or_log(&receipt_handle).await;
            return Ok(());
        };

        // TODO: render the report via Typst here — completes immediately
        // for now, to prove the claim/complete plumbing end to end.
        match self
            .request_service
            .complete(request_id, &self.worker_id, None)
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
}
