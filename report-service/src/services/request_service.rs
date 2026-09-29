use uuid::Uuid;

use crate::dto::request::Request;
use crate::repositories::request_repository::RequestRepository;

/// Thin for now — a direct pass-through to `RequestRepository`. Will grow to
/// compose request-claiming with attempt-tracking in one transaction once
/// that lands, the same way `RequestService` does on the Python side.
pub struct RequestService {
    repository: RequestRepository,
}

impl RequestService {
    #[must_use]
    pub fn new(repository: RequestRepository) -> Self {
        Self { repository }
    }

    pub async fn claim(
        &self,
        request_id: Uuid,
        worker_id: &str,
        lock_duration: chrono::Duration,
    ) -> sqlx::Result<Option<Request>> {
        self.repository
            .claim(request_id, worker_id, lock_duration)
            .await
    }

    pub async fn complete(
        &self,
        request_id: Uuid,
        worker_id: &str,
        result_item_id: Option<i32>,
    ) -> sqlx::Result<bool> {
        self.repository
            .complete(request_id, worker_id, result_item_id)
            .await
    }

    pub async fn retry_or_fail(
        &self,
        request_id: Uuid,
        worker_id: &str,
        is_terminal: bool,
    ) -> sqlx::Result<bool> {
        self.repository
            .retry_or_fail(request_id, worker_id, is_terminal)
            .await
    }
}
