"""add_user_digest_preferences

Revision ID: 71a9702ebdce
Revises: e4b5bfba1a89
Create Date: 2025-12-07 17:34:37.032029

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# заменяешь на реальные значения:
revision = "71a9702ebdce"
down_revision = "e4b5bfba1a89"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "digest_interests",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
    )
    op.add_column(
        "users",
        sa.Column(
            "digest_length_preference",
            sa.String(length=16),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("users", "digest_length_preference")
    op.drop_column("users", "digest_interests")
