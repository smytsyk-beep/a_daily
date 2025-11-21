"""add locale and timezone to users

Revision ID: c41b8f4d967c
Revises: 61af332f7d2c
Create Date: 2025-11-21 10:03:39.734665

"""

# alembic/versions/xxxx_add_locale_timezone_to_users.py

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "c41b8f4d967c"
down_revision = "61af332f7d2c"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("timezone", sa.String(length=64), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("users", "timezone")
