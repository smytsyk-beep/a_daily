"""seed

Revision ID: 1a4e02e08378
Revises: 80c706a1e657
Create Date: 2025-11-12 21:01:16.821217

"""
from typing import Sequence, Union

from alembic import op
from sqlalchemy.sql import text


# revision identifiers, used by Alembic.
revision: str = '1a4e02e08378'
down_revision: Union[str, Sequence[str], None] = '80c706a1e657'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade():
    # system: фиксированный id=1
    op.execute(text("""
        INSERT INTO users (id, tg_user_id, locale)
        VALUES (1, 'system', 'en')
        ON CONFLICT (id) DO NOTHING
    """))

    # demo: по tg_user_id (есть уникальный индекс)
    op.execute(text("""
        INSERT INTO users (tg_user_id, locale)
        VALUES ('demo', 'en')
        ON CONFLICT (tg_user_id) DO NOTHING
    """))
    # Если имя unique-индекса иное, можно так:
    # ON CONFLICT (tg_user_id) DO NOTHING
    # ON CONFLICT ON CONSTRAINT ix_users_tg_user_id DO NOTHING

def downgrade():
    # осторожно: если на system уже ссылаются FK — удалять нельзя.
    op.execute(text("DELETE FROM users WHERE tg_user_id = 'demo'"))
    op.execute(text("DELETE FROM users WHERE id = 1 AND tg_user_id = 'system'"))