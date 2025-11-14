# tests/test_orchestrator_resilience.py
from fastapi.testclient import TestClient
from app.main import app
from app import orchestrator as orch
from app.repo import session_scope
from app.models import ModuleRegistry
from app.repo import recent_events

client = TestClient(app)


def _boom(_user_id: str):
    raise RuntimeError("boom")


def test_orchestrator_survives_broken_module(monkeypatch):
    # Регистрируем модуль в БД
    with session_scope() as db:
        # создаём/находим запись
        row = db.query(ModuleRegistry).filter(ModuleRegistry.module == "boom").first()
        if not row:
            row = ModuleRegistry(module="boom", enabled=True, config=None)
            db.add(row)
            db.commit()
        else:
            row.enabled = True
            db.commit()

    # Подменяем карту модулей функцией, которая падает
    monkeypatch.setitem(orch.MODULES, "boom", _boom)

    data = orch.run_preview(user_id="resilience")
    assert data["ok"] is True
    assert isinstance(data["atoms"], list)
    assert "text" in data  # текст рендера есть

    # А событие предпросмотра действительно залогировано
    with session_scope() as db:
        items = recent_events(db, limit=1)
        assert items and items[0].event_ref == "preview_rendered"

    # Чистим за собой
    with session_scope() as db:
        row = db.query(ModuleRegistry).filter(ModuleRegistry.module == "boom").first()
        if row:
            db.delete(row)
            db.commit()
    orch.MODULES.pop("boom", None)
