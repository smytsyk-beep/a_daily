"""add geocode_cache

Revision ID: 4feab7d6b605
Revises: 773af91a7e19
Create Date: 2025-12-19 18:47:45.200381

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "4feab7d6b605"
down_revision: Union[str, Sequence[str], None] = "773af91a7e19"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.create_table(
        "geocode_cache",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("place_norm", sa.String(length=256), nullable=False),
        sa.Column("query_raw", sa.String(length=256), nullable=True),
        sa.Column("lat", sa.Float(), nullable=False),
        sa.Column("lon", sa.Float(), nullable=False),
        sa.Column("display_name", sa.String(length=512), nullable=True),
        sa.Column("provider", sa.String(length=32), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
    )
    op.create_index(
        "ix_geocode_cache_place_norm", "geocode_cache", ["place_norm"], unique=True
    )


def downgrade():
    op.drop_index("ix_geocode_cache_place_norm", table_name="geocode_cache")
    op.drop_table("geocode_cache")
