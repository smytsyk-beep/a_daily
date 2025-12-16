"""extend content_atoms with semantic matrix fields

Revision ID: e4b5bfba1a89
Revises: 5cc149008f01
Create Date: 2025-12-07 16:37:49.647750

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# заменишь на реальные ID
revision = "e4b5bfba1a89"
down_revision = "5cc149008f01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "content_atoms",
        sa.Column("trigger", sa.String(), nullable=True),
    )
    op.add_column(
        "content_atoms",
        sa.Column("house_tags", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.add_column(
        "content_atoms",
        sa.Column(
            "persona_tags", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
    )
    op.add_column(
        "content_atoms",
        sa.Column("strength_hint", sa.String(), nullable=True),
    )
    op.add_column(
        "content_atoms",
        sa.Column("copy_short", sa.Text(), nullable=True),
    )
    op.add_column(
        "content_atoms",
        sa.Column("copy_long", sa.Text(), nullable=True),
    )
    op.add_column(
        "content_atoms",
        sa.Column("cta", sa.Text(), nullable=True),
    )
    # по желанию можно повесить индекс на trigger
    op.create_index(
        "ix_content_atoms_trigger",
        "content_atoms",
        ["trigger"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_content_atoms_trigger", table_name="content_atoms")
    op.drop_column("content_atoms", "cta")
    op.drop_column("content_atoms", "copy_long")
    op.drop_column("content_atoms", "copy_short")
    op.drop_column("content_atoms", "strength_hint")
    op.drop_column("content_atoms", "persona_tags")
    op.drop_column("content_atoms", "house_tags")
    op.drop_column("content_atoms", "trigger")
