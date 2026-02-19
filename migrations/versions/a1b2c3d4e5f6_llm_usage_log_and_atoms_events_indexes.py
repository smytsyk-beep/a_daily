"""llm_usage_log and content_atoms/events indexes

Revision ID: a1b2c3d4e5f6
Revises: 4feab7d6b605
Create Date: 2026-02-19

- Table llm_usage_log for cost tracking.
- GIN index on content_atoms.persona_tags for fast tag filtering.
- Composite index on events (user_id, details->>'local_date') for daily digest lookups.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "4feab7d6b605"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # --- llm_usage_log: мониторинг затрат на LLM ---
    op.create_table(
        "llm_usage_log",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("model", sa.String(64), nullable=False),
        sa.Column("prompt_tokens", sa.Integer(), nullable=False),
        sa.Column("completion_tokens", sa.Integer(), nullable=False),
        sa.Column("estimated_cost_usd", sa.Numeric(10, 6), nullable=False),
        sa.Column("cache_hit", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_llm_usage_log__created_at", "llm_usage_log", ["created_at"])
    op.create_index("ix_llm_usage_log__user_id", "llm_usage_log", ["user_id"])

    # --- content_atoms: GIN по persona_tags (JSONB array) ---
    op.execute(
        "CREATE INDEX ix_content_atoms__persona_tags_gin ON content_atoms USING gin (persona_tags)"
    )

    # --- events: индекс для выборки по user_id + local_date (expression index) ---
    op.execute(
        "CREATE INDEX ix_events__user_id__local_date ON events (user_id, ((details->>'local_date')))"
    )


def downgrade():
    op.execute("DROP INDEX IF EXISTS ix_events__user_id__local_date")
    op.execute("DROP INDEX IF EXISTS ix_content_atoms__persona_tags_gin")

    op.drop_index("ix_llm_usage_log__user_id", table_name="llm_usage_log")
    op.drop_index("ix_llm_usage_log__created_at", table_name="llm_usage_log")
    op.drop_table("llm_usage_log")
