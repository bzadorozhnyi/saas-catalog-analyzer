use chrono::{DateTime, Utc};
use serde_json::Value as JsonValue;
use uuid::Uuid;

use crate::enums::request_status_enum::RequestStatus;
use crate::enums::request_type_enum::RequestType;

#[derive(Debug, sqlx::FromRow)]
pub struct Request {
    pub id: Uuid,
    pub request_type: RequestType,
    pub status: RequestStatus,
    pub payload: JsonValue,
    pub locked_by: Option<String>,
    pub locked_until: Option<DateTime<Utc>>,
    pub trace_id: Option<String>,
}
