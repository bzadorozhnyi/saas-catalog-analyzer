#[derive(Debug, Clone, Copy, PartialEq, Eq, sqlx::Type)]
#[sqlx(type_name = "requesttypeenum", rename_all = "SCREAMING_SNAKE_CASE")]
pub enum RequestType {
    CatalogCreation,
    GenerateReport,
}
