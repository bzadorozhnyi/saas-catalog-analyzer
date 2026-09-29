use chrono::{DateTime, Utc};
use uuid::Uuid;

#[derive(Debug, sqlx::FromRow)]
pub struct DuplicateCheck {
    pub id: Uuid,
    pub subscription_names: Vec<String>,
    pub duplicate_threshold: f64,
    pub review_threshold: f64,
    pub created_at: DateTime<Utc>,
}
