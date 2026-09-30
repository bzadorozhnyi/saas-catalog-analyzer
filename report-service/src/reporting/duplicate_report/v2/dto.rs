use chrono::{DateTime, Utc};
use serde::Serialize;
use uuid::Uuid;

/// The exact JSON shape `templates/duplicate_report_v2.typ` reads via
/// `json("data.json")`. Same fields as `v1::dto::ReportData` today, but
/// deliberately not shared with it — a version's payload shape is free to
/// diverge later without touching v1.
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
