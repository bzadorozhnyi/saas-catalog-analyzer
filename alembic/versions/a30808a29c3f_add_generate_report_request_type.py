"""add generate report request type

Revision ID: a30808a29c3f
Revises: 55aca7070f18
Create Date: 2026-09-29 10:57:58.788330

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a30808a29c3f"
down_revision: str | Sequence[str] | None = "55aca7070f18"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # Alembic autogenerate does not detect new values on an existing Postgres
    # enum type, so this is written by hand.
    op.execute("ALTER TYPE requesttypeenum ADD VALUE 'GENERATE_REPORT'")


def downgrade() -> None:
    """Downgrade schema."""
    # Postgres has no ALTER TYPE ... DROP VALUE — removing a single enum
    # value requires recreating the type entirely. Not supported here;
    # rolling back past this revision requires a manual data migration if
    # any GENERATE_REPORT rows exist.
    pass
