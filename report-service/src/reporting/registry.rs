use uuid::Uuid;

use crate::reporting::context::ReportingContext;
use crate::reporting::duplicate_report;

pub struct RenderRequest {
    pub template_path: &'static str,
    pub data_json: Vec<u8>,
}

/// Maps a (kind, version) pair from a `GENERATE_REPORT` request's payload to
/// the version-specific `build()` function and its `.typ` template. Each
/// match arm may call a differently-typed `build()`, since it serializes to
/// bytes immediately — adding a new report kind or version only means adding
/// a new arm here plus its own module, never touching existing ones.
pub async fn build_report(
    context: &ReportingContext,
    kind: &str,
    version: &str,
    check_id: Uuid,
) -> anyhow::Result<RenderRequest> {
    match (kind, version) {
        ("duplicate_detection", "v1") => {
            let data = duplicate_report::v1::build(context, check_id).await?;
            Ok(RenderRequest {
                template_path: "duplicate_report_v1.typ",
                data_json: serde_json::to_vec(&data)?,
            })
        }
        _ => anyhow::bail!("unknown report kind/version: {kind}/{version}"),
    }
}
