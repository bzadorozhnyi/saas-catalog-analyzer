use chrono::{DateTime, Utc};
use serde::Serialize;
use uuid::Uuid;

/// The exact JSON shape `templates/duplicate_report_v1.typ` reads via
/// `json("data.json")`. Owned by this version specifically — a future v2
/// gets its own `v2::dto` rather than reusing this, since the payload shape
/// is allowed to change between versions.
#[derive(Serialize)]
pub struct ReportData {
    pub check_id: Uuid,
    pub subscription_names: Vec<String>,
    pub duplicate_threshold: f64,
    pub review_threshold: f64,
    pub created_at: DateTime<Utc>,
    pub pairs: Vec<PairData>,
}

#[derive(Serialize)]
pub struct PairData {
    pub name_a: String,
    pub name_b: String,
    pub similarity: f64,
    pub verdict: String,
    pub is_duplicate: Option<bool>,
    pub confidence: Option<f64>,
    pub reasoning: Option<String>,
    pub overlapping_features: Option<Vec<String>>,
}
