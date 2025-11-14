from alembic import op

# ревизии
revision = "cf3fc75edb70"  # ALEMBIC заполнит при создании файла
down_revision = "dc288b25cbc0"  # твой seed-ревиз предыдущего шага
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Идемпотентная вставка: добавляем строки, если их ещё нет.
    op.execute(
        """
    INSERT INTO module_registry (module, enabled, config)
    SELECT v.module, v.enabled, v.config
    FROM (VALUES
       ('daily_digest', TRUE, '{}'::jsonb),
       ('strong_events_alerts', TRUE, '{}'::jsonb)
    ) AS v(module, enabled, config)
    WHERE NOT EXISTS (
        SELECT 1 FROM module_registry m WHERE m.module = v.module
    );
    """
    )


def downgrade() -> None:
    op.execute(
        """
    DELETE FROM module_registry
    WHERE module IN ('daily_digest','strong_events_alerts');
    """
    )
