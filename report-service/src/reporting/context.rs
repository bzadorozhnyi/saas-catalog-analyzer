use crate::repositories::duplicate_repository::DuplicateRepository;

/// Bundles every repository a report `build()` function might need. Add a
/// new field here when a report genuinely needs a new data source — a
/// version's `build()` picks out only what it uses, so this growing does not
/// change the signature of `build_report()` or of unrelated `build()`
/// functions.
pub struct ReportingContext {
    pub duplicate_repository: DuplicateRepository,
}
