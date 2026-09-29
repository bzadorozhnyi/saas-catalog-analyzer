use sqlx::PgPool;
use uuid::Uuid;

use crate::dto::duplicate_check::DuplicateCheck;
use crate::dto::duplicate_pair::DuplicatePair;

pub struct DuplicateRepository {
    pool: PgPool,
}

impl DuplicateRepository {
    #[must_use]
    pub fn new(pool: PgPool) -> Self {
        Self { pool }
    }

    pub async fn get_check(&self, check_id: Uuid) -> sqlx::Result<Option<DuplicateCheck>> {
        sqlx::query_as!(
            DuplicateCheck,
            r#"
            SELECT id, subscription_names, duplicate_threshold, review_threshold, created_at
            FROM duplicate_checks
            WHERE id = $1
            "#,
            check_id,
        )
        .fetch_optional(&self.pool)
        .await
    }

    pub async fn list_pairs(&self, check_id: Uuid) -> sqlx::Result<Vec<DuplicatePair>> {
        sqlx::query_as!(
            DuplicatePair,
            r#"
            SELECT
                id,
                name_a,
                name_b,
                similarity,
                verdict::text AS "verdict!",
                is_duplicate,
                confidence,
                reasoning,
                overlapping_features
            FROM duplicate_pairs
            WHERE check_id = $1
            ORDER BY similarity DESC
            "#,
            check_id,
        )
        .fetch_all(&self.pool)
        .await
    }
}
