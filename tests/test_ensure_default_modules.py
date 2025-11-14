# tests/test_ensure_default_modules.py

from app.repo import session_scope, ensure_default_modules
from app.models import ModuleRegistry


def test_ensure_default_modules_persists_and_is_idempotent():
    # 0) Чистим таблицу и коммитим (важно!)
    with session_scope() as db:
        db.query(ModuleRegistry).delete(synchronize_session=False)
        db.commit()

    # 1) Первый запуск сидера + проверка в НОВОЙ сессии
    with session_scope() as db:
        ensure_default_modules(db)

    with session_scope() as db:
        rows = db.query(ModuleRegistry).order_by(ModuleRegistry.module).all()
        mods = [r.module for r in rows]

    assert "daily_digest" in mods
    assert "strong_events_alerts" in mods
    assert len(mods) == 2  # ожидаем ровно 2 записи

    # 2) Повторный запуск сидера не должен создавать дубликаты
    with session_scope() as db:
        ensure_default_modules(db)

    with session_scope() as db:
        rows2 = db.query(ModuleRegistry).order_by(ModuleRegistry.module).all()
        mods2 = [r.module for r in rows2]

    assert mods2 == mods  # состав и порядок те же
    assert len(mods2) == 2
