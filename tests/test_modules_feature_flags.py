# tests/test_modules_feature_flags.py
from fastapi.testclient import TestClient
from app.main import app
from app.repo import session_scope
from app.models import ModuleRegistry
from app.orchestrator import run_preview

client = TestClient(app)


def test_feature_flag_disables_module():
    # Базовая выборка при включённых модулях
    base = run_preview(user_id="ff_base")
    base_count = len(base["atoms"])
    assert base_count > 0
    assert "strong_events_alerts" in base["modules"]

    with session_scope() as db:
        row = (
            db.query(ModuleRegistry)
            .filter(ModuleRegistry.module == "strong_events_alerts")
            .first()
        )
        assert row is not None, "seed должен был создать запись strong_events_alerts"
        original = row.enabled
        try:
            # Выключаем модуль
            row.enabled = False
            db.commit()

            after = run_preview(user_id="ff_disabled")
            assert "strong_events_alerts" not in after["modules"]
            assert len(after["atoms"]) < base_count
        finally:
            # Возвращаем как было
            row.enabled = original
            db.commit()
