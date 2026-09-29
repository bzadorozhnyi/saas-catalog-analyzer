use uuid::Uuid;

#[derive(Debug, sqlx::FromRow)]
pub struct DuplicatePair {
    pub id: Uuid,
    pub name_a: String,
    pub name_b: String,
    pub similarity: f64,
    pub verdict: String,
    pub is_duplicate: Option<bool>,
    pub confidence: Option<f64>,
    pub reasoning: Option<String>,
    pub overlapping_features: Option<Vec<String>>,
}
