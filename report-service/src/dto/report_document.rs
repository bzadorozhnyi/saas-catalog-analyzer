use chrono::{DateTime, Utc};
use uuid::Uuid;

#[derive(Debug, sqlx::FromRow)]
pub struct ReportDocument {
    pub id: i32,
    pub request_id: Uuid,
    pub blob_name: String,
    pub created_at: DateTime<Utc>,
}
