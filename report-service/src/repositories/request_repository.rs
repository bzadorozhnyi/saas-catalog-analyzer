use chrono::Utc;
use sqlx::PgExecutor;
use uuid::Uuid;

use crate::dto::request::Request;
use crate::enums::request_status_enum::RequestStatus;
use crate::enums::request_type_enum::RequestType;

/// Every method takes its executor as a parameter instead of holding a
/// `PgPool` — see `RequestAttemptRepository` for why: `RequestService`
/// always composes these calls with the attempt-tracking repository in one
/// transaction.
pub struct RequestRepository;

impl RequestRepository {
    /// Atomically claims a request: succeeds when the row is `QUEUED`,
    /// `FAILED` (not terminal — see `fail()`), or `PROCESSING` with an
    /// expired lock (a worker that died mid-attempt). `FAILED` rows have no
    /// active lock (`fail()` clears it), so — unlike the `PROCESSING`
    /// branch — there's no lock to wait out; nothing is currently working
    /// on them. Mirrors `RequestRepository.claim()` on the Python side
    /// exactly.
    pub async fn claim(
        executor: impl PgExecutor<'_>,
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
              AND (
                status = 'QUEUED'
                OR status = 'FAILED'
                OR (status = 'PROCESSING' AND locked_until < now())
              )
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
        .fetch_optional(executor)
        .await
    }

    /// Marks a claimed request completed. Only succeeds while `worker_id`
    /// still holds the lock (guards against a lock lost to another worker).
    pub async fn complete(
        executor: impl PgExecutor<'_>,
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
        .execute(executor)
        .await?;
        Ok(result.rows_affected() == 1)
    }

    /// Not terminal — see `claim()`. Whether this request gets another
    /// attempt is entirely up to SQS (redelivery) or a manual DLQ redrive;
    /// neither touches this table.
    pub async fn fail(
        executor: impl PgExecutor<'_>,
        request_id: Uuid,
        worker_id: &str,
    ) -> sqlx::Result<bool> {
        let result = sqlx::query!(
            r#"
            UPDATE requests
            SET status = 'FAILED', locked_by = NULL, locked_until = NULL
            WHERE id = $1 AND locked_by = $2
            "#,
            request_id,
            worker_id,
        )
        .execute(executor)
        .await?;
        Ok(result.rows_affected() == 1)
    }
}
