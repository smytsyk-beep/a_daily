import uuid

from sqlalchemy import insert

from app.db import SessionLocal
from app import models
from app.orchestrator import run_preview, MODULES


def test_orchestrator_uses_content_atoms_locale():
    db = SessionLocal()

    # уникальные имена, чтобы не ловить UniqueViolation между прогоном тестов
    user_alias = f"ml_user_{uuid.uuid4().hex}"
    module_name = f"dummy_ml_{uuid.uuid4().hex}"

    # dummy-модуль, который возвращает атом без text, только topic_tag
    def dummy_module(user_id: str, config: dict | None = None):
        return [
            {
                "module": module_name,
                "kind": "test",
                "topic_tag": "ml_test_tag",
                "weight": 1.0,
            }
        ]

    # временно подменяем список модулей
    original_modules = MODULES.copy()
    MODULES.clear()
    MODULES[module_name] = dummy_module

    try:
        # пользователь с локалью ru
        user = models.User(tg_user_id=user_alias, locale="ru")
        db.add(user)
        db.commit()
        db.refresh(user)

        # контент-атом для ru
        db.execute(
            insert(models.ContentAtom).values(
                locale="ru",
                topic_tag="ml_test_tag",
                style="neutral",
                body="RU TEXT BODY",
            )
        )
        db.commit()

        # регистрируем модуль в ModuleRegistry с тем же именем, что и в MODULES
        db.add(models.ModuleRegistry(module=module_name, enabled=True, config={}))
        db.commit()

        resp = run_preview(user_alias)

        assert resp["ok"] is True

        texts = [a.get("text") for a in resp["atoms"]]
        # текст должен быть подставлен из ContentAtom
        assert "RU TEXT BODY" in texts
        assert "RU TEXT BODY" in resp["text"]
    finally:
        MODULES.clear()
        MODULES.update(original_modules)
        db.close()
