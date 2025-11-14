"""fix: ensure default modules present
Revision ID: 61af332f7d2c
Revises: cf3fc75edb70
Create Date: 2025-11-14 21:02:22.661336
"""

from alembic import op

revision = "61af332f7d2c"  # alembic
down_revision = "cf3fc75edb70"  # ВАЖНО: cf3fc75edb70
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        INSERT INTO module_registry (module, enabled, config) VALUES
            ('daily_digest', TRUE, '{}'::jsonb),
            ('strong_events_alerts', TRUE, '{}'::jsonb)
        ON CONFLICT (module) DO NOTHING;
    """
    )


def downgrade() -> None:
    # мягкий откат — удаляем, если именно эти строки были добавлены
    op.execute(
        """
        DELETE FROM module_registry
        WHERE module IN ('daily_digest','strong_events_alerts');
    """
    )
