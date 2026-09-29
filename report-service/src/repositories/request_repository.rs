use chrono::Utc;
use sqlx::PgPool;
use uuid::Uuid;

use crate::dto::request::Request;
use crate::enums::request_status_enum::RequestStatus;
use crate::enums::request_type_enum::RequestType;

pub struct RequestRepository {
    pool: PgPool,
}

impl RequestRepository {
    #[must_use]
    pub fn new(pool: PgPool) -> Self {
        Self { pool }
    }

    /// Atomically claims a request: succeeds only when the row is `QUEUED`,
    /// or `PROCESSING` with an expired lock (a worker that died mid-attempt).
    /// Mirrors `RequestRepository.claim()` on the Python side exactly.
    pub async fn claim(
        &self,
        request_id: Uuid,
        worker_id: &str,
        lock_duration: chrono::Duration,
    ) -> sqlx::Result<Option<Request>> {
        let locked_until = Utc::now() + lock_duration;
        sqlx::query_as!(
            Request,
            r#"
            UPDATE requests
            SET status = 'PROCESSING', locked_by = $2, locked_until = $3
            WHERE id = $1
              AND (status = 'QUEUED' OR (status = 'PROCESSING' AND locked_until < now()))
            RETURNING
                id,
                request_type AS "request_type: RequestType",
                status AS "status: RequestStatus",
                payload,
                locked_by,
                locked_until
            "#,
            request_id,
            worker_id,
            locked_until,
        )
        .fetch_optional(&self.pool)
        .await
    }

    /// Marks a claimed request completed. Only succeeds while `worker_id`
    /// still holds the lock (guards against a lock lost to another worker).
    pub async fn complete(
        &self,
        request_id: Uuid,
        worker_id: &str,
        result_item_id: Option<i32>,
    ) -> sqlx::Result<bool> {
        let result = sqlx::query!(
            r#"
            UPDATE requests
            SET status = 'COMPLETED', result_item_id = $3, locked_by = NULL, locked_until = NULL
            WHERE id = $1 AND locked_by = $2
            "#,
            request_id,
            worker_id,
            result_item_id,
        )
        .execute(&self.pool)
        .await?;
        Ok(result.rows_affected() == 1)
    }

    /// Releases a claimed request back to `PENDING` for another dispatch
    /// cycle, or marks it `FAILED` when `is_terminal` (attempts exhausted).
    pub async fn retry_or_fail(
        &self,
        request_id: Uuid,
        worker_id: &str,
        is_terminal: bool,
    ) -> sqlx::Result<bool> {
        let status = if is_terminal {
            RequestStatus::Failed
        } else {
            RequestStatus::Pending
        };
        let result = sqlx::query!(
            r#"
            UPDATE requests
            SET status = $3, locked_by = NULL, locked_until = NULL
            WHERE id = $1 AND locked_by = $2
            "#,
            request_id,
            worker_id,
            status as RequestStatus,
        )
        .execute(&self.pool)
        .await?;
        Ok(result.rows_affected() == 1)
    }
}
