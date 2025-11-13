from alembic.config import Config
from alembic import command
from app.db import SessionLocal
from app.models import User
import os

def test_seed_is_idempotent():
    """
    Прогоняем alembic upgrade head дважды и проверяем,
    что сид-пользователи ('system', 'demo') созданы ровно по одному разу,
    а 'system' имеет id=1 и tg_user_id уникальны.
    """
    cfg = Config(os.path.join(os.getcwd(), "alembic.ini"))

    # дважды — должно быть безопасно
    command.upgrade(cfg, "head")
    command.upgrade(cfg, "head")

    db = SessionLocal()
    try:
        users = db.query(User).order_by(User.id).all()

        system = [u for u in users if u.tg_user_id == "system"]
        demo   = [u for u in users if u.tg_user_id == "demo"]

        # сиды существуют по одному разу
        assert len(system) == 1
        assert len(demo) == 1

        # system всегда id=1
        assert system[0].id == 1

        # tg_user_id уникальны
        tg_ids = [u.tg_user_id for u in users]
        assert len(tg_ids) == len(set(tg_ids))
    finally:
        db.close()