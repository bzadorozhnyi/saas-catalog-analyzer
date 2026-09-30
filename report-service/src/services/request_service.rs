use chrono::Duration;
use sqlx::PgPool;
use uuid::Uuid;

use crate::dto::request::Request;
use crate::dto::request_attempt::RequestAttempt;
use crate::repositories::request_attempt_repository::RequestAttemptRepository;
use crate::repositories::request_repository::RequestRepository;

/// Composes `RequestRepository` and `RequestAttemptRepository` in a single
/// transaction per operation — a claim and its attempt row (or a
/// completion/failure and its attempt row) must commit or roll back
/// together, the same guarantee `RequestService` gives on the Python side
/// via a shared `AsyncSession`.
pub struct RequestService {
    pool: PgPool,
}

impl RequestService {
    #[must_use]
    pub fn new(pool: PgPool) -> Self {
        Self { pool }
    }

    pub async fn claim(
        &self,
        request_id: Uuid,
        worker_id: &str,
        lock_duration: Duration,
    ) -> sqlx::Result<Option<(Request, RequestAttempt)>> {
        let mut tx = self.pool.begin().await?;

        let Some(request) =
            RequestRepository::claim(&mut *tx, request_id, worker_id, lock_duration).await?
        else {
            tx.rollback().await?;
            return Ok(None);
        };

        let attempt_number =
            RequestAttemptRepository::count_for_request(&mut *tx, request_id).await? + 1;
        let attempt = RequestAttemptRepository::start(
            &mut *tx,
            request_id,
            i32::try_from(attempt_number).unwrap_or(i32::MAX),
        )
        .await?;

        tx.commit().await?;
        Ok(Some((request, attempt)))
    }

    pub async fn complete(
        &self,
        request_id: Uuid,
        worker_id: &str,
        attempt_id: Uuid,
        result_item_id: Option<i32>,
        success_message: &str,
    ) -> sqlx::Result<bool> {
        let mut tx = self.pool.begin().await?;

        let completed =
            RequestRepository::complete(&mut *tx, request_id, worker_id, result_item_id).await?;
        if completed {
            RequestAttemptRepository::succeed(&mut *tx, attempt_id, success_message).await?;
        }

        tx.commit().await?;
        Ok(completed)
    }

    /// Not terminal — see `RequestRepository::claim()`/`fail()`. How many
    /// more times this gets tried is SQS's call (redelivery +
    /// `RedrivePolicy`), not ours; we just record what happened.
    pub async fn fail(
        &self,
        request_id: Uuid,
        worker_id: &str,
        attempt_id: Uuid,
        error_message: &str,
    ) -> sqlx::Result<bool> {
        let mut tx = self.pool.begin().await?;

        let updated = RequestRepository::fail(&mut *tx, request_id, worker_id).await?;
        if updated {
            RequestAttemptRepository::fail(&mut *tx, attempt_id, error_message).await?;
        }

        tx.commit().await?;
        Ok(updated)
    }
}
