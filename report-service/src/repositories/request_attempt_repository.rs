use sqlx::PgExecutor;
use uuid::Uuid;

use crate::dto::request_attempt::RequestAttempt;
use crate::enums::attempt_status_enum::AttemptStatus;

pub struct RequestAttemptRepository;

impl RequestAttemptRepository {
    pub async fn count_for_request(
        executor: impl PgExecutor<'_>,
        request_id: Uuid,
    ) -> sqlx::Result<i64> {
        sqlx::query_scalar!(
            r#"SELECT COUNT(*) AS "count!" FROM request_attempts WHERE request_id = $1"#,
            request_id,
        )
        .fetch_one(executor)
        .await
    }

    pub async fn start(
        executor: impl PgExecutor<'_>,
        request_id: Uuid,
        attempt_number: i32,
    ) -> sqlx::Result<RequestAttempt> {
        sqlx::query_as!(
            RequestAttempt,
            r#"
            INSERT INTO request_attempts (id, request_id, attempt_number, status)
            VALUES ($1, $2, $3, 'STARTED')
            RETURNING
                id,
                request_id,
                attempt_number,
                status AS "status: AttemptStatus",
                error_message,
                success_message,
                trace_id,
                started_at,
                finished_at
            "#,
            Uuid::new_v4(),
            request_id,
            attempt_number,
        )
        .fetch_one(executor)
        .await
    }

    pub async fn succeed(
        executor: impl PgExecutor<'_>,
        attempt_id: Uuid,
        success_message: &str,
        trace_id: Option<&str>,
    ) -> sqlx::Result<()> {
        sqlx::query!(
            r#"
            UPDATE request_attempts
            SET status = 'SUCCEEDED', success_message = $2, trace_id = $3, finished_at = now()
            WHERE id = $1
            "#,
            attempt_id,
            success_message,
            trace_id,
        )
        .execute(executor)
        .await?;
        Ok(())
    }

    pub async fn fail(
        executor: impl PgExecutor<'_>,
        attempt_id: Uuid,
        error_message: &str,
        trace_id: Option<&str>,
    ) -> sqlx::Result<()> {
        sqlx::query!(
            r#"
            UPDATE request_attempts
            SET status = 'FAILED', error_message = $2, trace_id = $3, finished_at = now()
            WHERE id = $1
            "#,
            attempt_id,
            error_message,
            trace_id,
        )
        .execute(executor)
        .await?;
        Ok(())
    }
}
