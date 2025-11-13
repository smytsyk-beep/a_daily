from alembic import op
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = "1a4e02e08378"
down_revision = "80c706a1e657"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()

    # 1) system с фиксированным id=1 (идемпотентно)
    conn.execute(
        text(
            """
        INSERT INTO users (id, tg_user_id, locale)
        VALUES (1, 'system', 'en')
        ON CONFLICT (id) DO NOTHING;
    """
        )
    )

    # 2) выравниваем последовательность на MAX(id) (минимум 1)
    conn.execute(
        text(
            """
        SELECT setval(
            pg_get_serial_sequence('users','id'),
            GREATEST((SELECT COALESCE(MAX(id), 0) FROM users), 1),
            true
        );
    """
        )
    )

    # 3) demo по tg_user_id (идемпотентно)
    conn.execute(
        text(
            """
        INSERT INTO users (tg_user_id, locale)
        VALUES ('demo', 'en')
        ON CONFLICT (tg_user_id) DO NOTHING;
    """
        )
    )


def downgrade():
    conn = op.get_bind()
    # удаляем только сиды
    conn.execute(
        text(
            """
        DELETE FROM users WHERE tg_user_id IN ('demo', 'system');
    """
        )
    )
