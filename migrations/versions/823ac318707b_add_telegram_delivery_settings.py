"""add telegram delivery settings to users

Revision ID: 823ac318707b
Revises: 71a9702ebdce
Create Date: 2025-12-07 19:41:31.952242

"""

from alembic import op
import sqlalchemy as sa


revision = "823ac318707b"
down_revision = "71a9702ebdce"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("delivery_time_local", sa.String(length=8), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("delivery_enabled", sa.Boolean(), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("quiet_mode", sa.Boolean(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("users", "quiet_mode")
    op.drop_column("users", "delivery_enabled")
    op.drop_column("users", "delivery_time_local")
