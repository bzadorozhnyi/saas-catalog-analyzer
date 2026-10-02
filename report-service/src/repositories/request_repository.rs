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

/// What came of a claim attempt when the straightforward `UPDATE` didn't
/// match any row. "Not claimed" used to mean one thing to callers (safe to
/// delete the SQS message) — it actually covers several different
/// situations that need different handling; see `RequestRepository::claim`.
pub enum ClaimAttempt {
    Claimed(Request),
    /// Row is still `PENDING` — the dispatcher's SQS send and its
    /// `mark_queued` commit aren't one atomic operation, so a message can
    /// legitimately arrive before the row is actually claimable yet. Not a
    /// duplicate: the caller should leave the message alone for SQS's own
    /// redelivery rather than deleting it.
    NotYetQueued,
    /// Row doesn't exist, is already `COMPLETED`, or is `PROCESSING` under
    /// another worker's still-live lock — in every case nothing further is
    /// needed from this message; safe to delete.
    Unclaimable,
}

impl RequestRepository {
    /// Atomically claims a request: succeeds when the row is `QUEUED`,
    /// `FAILED` (not terminal — see `fail()`), or `PROCESSING` with an
    /// expired lock (a worker that died mid-attempt). `FAILED` rows have no
    /// active lock (`fail()` clears it), so — unlike the `PROCESSING`
    /// branch — there's no lock to wait out; nothing is currently working
    /// on them.
    ///
    /// On a miss, falls back to a row-locking read (`SELECT ... FOR
    /// UPDATE`) to find out *why* — this blocks out any concurrent writer
    /// of this same row (the dispatcher's `mark_queued`, another worker's
    /// `complete`/`fail`) until we're done deciding, so the status we
    /// classify against can never be a stale snapshot racing against one of
    /// those writers. If it turns out to have become claimable in the gap
    /// between the first attempt and this locked read, we claim it right
    /// there instead of making the caller wait out an SQS redelivery cycle
    /// for something we can already see is ready. Requires `tx` to be an
    /// actual transaction (not a bare pool) — the row lock only holds for
    /// the lifetime of one.
    pub async fn claim(
        tx: &mut sqlx::PgConnection,
        request_id: Uuid,
        worker_id: &str,
        lock_duration: chrono::Duration,
    ) -> sqlx::Result<ClaimAttempt> {
        let locked_until = Utc::now() + lock_duration;

        if let Some(request) =
            Self::try_claim(&mut *tx, request_id, worker_id, locked_until).await?
        {
            return Ok(ClaimAttempt::Claimed(request));
        }

        let status = sqlx::query_scalar!(
            r#"SELECT status AS "status: RequestStatus" FROM requests WHERE id = $1 FOR UPDATE"#,
            request_id,
        )
        .fetch_optional(&mut *tx)
        .await?;

        match status {
            Some(RequestStatus::Pending) => Ok(ClaimAttempt::NotYetQueued),
            Some(RequestStatus::Queued | RequestStatus::Failed | RequestStatus::Processing) => {
                // Became claimable (or its lock expired) in the gap above —
                // we're still holding the row lock, so this is guaranteed
                // to see the same state we just read.
                match Self::try_claim(&mut *tx, request_id, worker_id, locked_until).await? {
                    Some(request) => Ok(ClaimAttempt::Claimed(request)),
                    None => Ok(ClaimAttempt::Unclaimable),
                }
            }
            Some(RequestStatus::Completed) | None => Ok(ClaimAttempt::Unclaimable),
        }
    }

    async fn try_claim(
        executor: impl PgExecutor<'_>,
        request_id: Uuid,
        worker_id: &str,
        locked_until: chrono::DateTime<Utc>,
    ) -> sqlx::Result<Option<Request>> {
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
                locked_until,
                trace_id,
                trace_context
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

    /// Keeps a claim alive past its original lock duration while a slow
    /// attempt (e.g. Typst rendering with a cold `@preview` package cache)
    /// is still in progress. Only succeeds while `worker_id` still holds
    /// the lock — `false` means it was already reclaimed by someone else,
    /// so the caller's heartbeat should stop. Mirrors
    /// `RequestRepository.extend_lock()` on the Python side.
    pub async fn extend_lock(
        executor: impl PgExecutor<'_>,
        request_id: Uuid,
        worker_id: &str,
        lock_duration: chrono::Duration,
    ) -> sqlx::Result<bool> {
        let locked_until = Utc::now() + lock_duration;
        let result = sqlx::query!(
            r#"
            UPDATE requests
            SET locked_until = $3
            WHERE id = $1 AND locked_by = $2 AND status = 'PROCESSING'
            "#,
            request_id,
            worker_id,
            locked_until,
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
