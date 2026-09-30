#[derive(Debug, Clone, Copy, PartialEq, Eq, sqlx::Type)]
#[sqlx(type_name = "attemptstatusenum", rename_all = "SCREAMING_SNAKE_CASE")]
pub enum AttemptStatus {
    Started,
    Succeeded,
    Failed,
}
