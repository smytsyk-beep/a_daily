from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as psql

# ревизии
revision = "<paste_new_rev>"
down_revision = "1a4e02e08378"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "feature_flags",
        sa.Column("key", sa.String(64), primary_key=True),
        sa.Column(
            "is_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")
        ),
        sa.Column("payload", psql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_feature_flags_enabled", "feature_flags", ["is_enabled"])

    op.create_table(
        "events",
        sa.Column("id", sa.BigInteger, primary_key=True),
        sa.Column(
            "user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="SET NULL")
        ),
        sa.Column("kind", sa.String(32), nullable=False),  # 'transit' | 'strong' | др.
        sa.Column(
            "ts",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("title", sa.String(256), nullable=False),
        sa.Column("details", psql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.create_index("ix_events_user_ts", "events", ["user_id", "ts"])
    op.create_index("ix_events_kind_ts", "events", ["kind", "ts"])


def downgrade():
    op.drop_index("ix_events_kind_ts", table_name="events")
    op.drop_index("ix_events_user_ts", table_name="events")
    op.drop_table("events")

    op.drop_index("ix_feature_flags_enabled", table_name="feature_flags")
    op.drop_table("feature_flags")
