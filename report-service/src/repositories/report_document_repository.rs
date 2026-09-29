use sqlx::PgPool;
use uuid::Uuid;

use crate::dto::report_document::ReportDocument;

pub struct ReportDocumentRepository {
    pool: PgPool,
}

impl ReportDocumentRepository {
    #[must_use]
    pub fn new(pool: PgPool) -> Self {
        Self { pool }
    }

    pub async fn create(&self, request_id: Uuid, blob_name: &str) -> sqlx::Result<ReportDocument> {
        sqlx::query_as!(
            ReportDocument,
            r#"
            INSERT INTO report_documents (request_id, blob_name)
            VALUES ($1, $2)
            RETURNING id, request_id, blob_name, created_at
            "#,
            request_id,
            blob_name,
        )
        .fetch_one(&self.pool)
        .await
    }
}
