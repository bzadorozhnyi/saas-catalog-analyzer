#[derive(Debug, Clone, Copy, PartialEq, Eq, sqlx::Type)]
#[sqlx(type_name = "requeststatusenum", rename_all = "SCREAMING_SNAKE_CASE")]
pub enum RequestStatus {
    Pending,
    Queued,
    Processing,
    Completed,
    Failed,
}
