use aws_sdk_sqs::types::Message;
use serde_json::Value;

/// `Clone` is cheap (`aws_sdk_sqs::Client` is `Arc`-backed internally) — the
/// heartbeat task in `ReportGenerationConsumer` clones this to extend the
/// SQS visibility timeout from its own `tokio::spawn`ed future.
#[derive(Clone)]
pub struct SqsService {
    client: aws_sdk_sqs::Client,
    queue_url: String,
}

impl SqsService {
    #[must_use]
    pub fn new(client: aws_sdk_sqs::Client, queue_url: String) -> Self {
        Self { client, queue_url }
    }

    pub async fn send_message(&self, body: &Value) -> Result<(), aws_sdk_sqs::Error> {
        self.client
            .send_message()
            .queue_url(&self.queue_url)
            .message_body(body.to_string())
            .send()
            .await?;
        Ok(())
    }

    pub async fn receive_messages(
        &self,
        max_messages: i32,
        wait_seconds: i32,
    ) -> Result<Vec<Message>, aws_sdk_sqs::Error> {
        let response = self
            .client
            .receive_message()
            .queue_url(&self.queue_url)
            .max_number_of_messages(max_messages)
            .wait_time_seconds(wait_seconds)
            .send()
            .await?;
        Ok(response.messages.unwrap_or_default())
    }

    pub async fn delete_message(&self, receipt_handle: &str) -> Result<(), aws_sdk_sqs::Error> {
        self.client
            .delete_message()
            .queue_url(&self.queue_url)
            .receipt_handle(receipt_handle)
            .send()
            .await?;
        Ok(())
    }

    pub async fn change_message_visibility(
        &self,
        receipt_handle: &str,
        visibility_timeout_seconds: i32,
    ) -> Result<(), aws_sdk_sqs::Error> {
        self.client
            .change_message_visibility()
            .queue_url(&self.queue_url)
            .receipt_handle(receipt_handle)
            .visibility_timeout(visibility_timeout_seconds)
            .send()
            .await?;
        Ok(())
    }
}
