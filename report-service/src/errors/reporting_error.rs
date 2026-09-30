use uuid::Uuid;

#[derive(thiserror::Error, Debug)]
pub enum ReportingError {
    #[error("duplicate check {0} not found")]
    CheckNotFound(Uuid),

    #[error("unknown report kind/version: {kind}/{version}")]
    UnknownReportKind { kind: String, version: String },

    #[error("invalid report request payload: {0}")]
    InvalidPayload(String),

    #[error(transparent)]
    Database(#[from] sqlx::Error),

    #[error(transparent)]
    Serialization(#[from] serde_json::Error),
}

impl ReportingError {
    /// Whether retrying the request could possibly succeed. `false` means
    /// the request itself is unfixable (bad `check_id`, unknown report
    /// kind/version) and should be failed rather than redelivered.
    #[must_use]
    pub fn is_retryable(&self) -> bool {
        matches!(self, Self::Database(_))
    }
}
