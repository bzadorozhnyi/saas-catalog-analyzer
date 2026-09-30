use chrono::{DateTime, Utc};
use uuid::Uuid;

use crate::enums::attempt_status_enum::AttemptStatus;

#[derive(Debug, sqlx::FromRow)]
pub struct RequestAttempt {
    pub id: Uuid,
    pub request_id: Uuid,
    pub attempt_number: i32,
    pub status: AttemptStatus,
    pub error_message: Option<String>,
    pub success_message: Option<String>,
    pub trace_id: Option<String>,
    pub started_at: DateTime<Utc>,
    pub finished_at: Option<DateTime<Utc>>,
}
