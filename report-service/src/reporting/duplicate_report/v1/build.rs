use uuid::Uuid;

use crate::reporting::context::ReportingContext;
use crate::reporting::duplicate_report::v1::dto::{PairData, ReportData};

/// Builds the report payload straight from already-persisted data — no LLM
/// calls, no dependency on the Python side. Everything needed was written by
/// `find_duplicates`/`explain_duplicate` at the time those were called.
pub async fn build(context: &ReportingContext, check_id: Uuid) -> anyhow::Result<ReportData> {
    let repository = &context.duplicate_repository;

    let check = repository
        .get_check(check_id)
        .await?
        .ok_or_else(|| anyhow::anyhow!("duplicate check {check_id} not found"))?;
    let pairs = repository.list_pairs(check_id).await?;

    Ok(ReportData {
        check_id: check.id,
        subscription_names: check.subscription_names,
        duplicate_threshold: check.duplicate_threshold,
        review_threshold: check.review_threshold,
        created_at: check.created_at,
        pairs: pairs
            .into_iter()
            .map(|pair| PairData {
                name_a: pair.name_a,
                name_b: pair.name_b,
                similarity: pair.similarity,
                verdict: pair.verdict,
                is_duplicate: pair.is_duplicate,
                confidence: pair.confidence,
                reasoning: pair.reasoning,
                overlapping_features: pair.overlapping_features,
            })
            .collect(),
    })
}
