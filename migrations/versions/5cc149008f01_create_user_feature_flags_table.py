"""create user_feature_flags table

Revision ID: 5cc149008f01
Revises: c41b8f4d967c
Create Date: 2025-11-21 09:39:59.667036

"""

from alembic import op
import sqlalchemy as sa

revision = "5cc149008f01"
down_revision = "c41b8f4d967c"  # это id миграции events_feature_flags; подставь свой
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "user_feature_flags",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "feature_key",
            sa.String(length=64),
            sa.ForeignKey("feature_flags.key", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("enabled", sa.Boolean(), nullable=False),
    )

    op.create_unique_constraint(
        "uq_user_feature_flag",
        "user_feature_flags",
        ["user_id", "feature_key"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_user_feature_flag", "user_feature_flags", type_="unique")
    op.drop_table("user_feature_flags")
