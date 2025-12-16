"""extend users with prefs and consents

Revision ID: 773af91a7e19
Revises: 823ac318707b
Create Date: 2025-12-14 11:50:16.836188

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "773af91a7e19"
down_revision = "823ac318707b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("display_name", sa.String(), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("age_gate_accepted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("disclaimer_accepted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("birthdata_consent_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column(
            "prefs",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("users", "prefs")
    op.drop_column("users", "birthdata_consent_at")
    op.drop_column("users", "disclaimer_accepted_at")
    op.drop_column("users", "age_gate_accepted_at")
    op.drop_column("users", "display_name")
