from datetime import datetime
from typing import List, Dict

from app.repo import (
    session_scope,
    list_enabled_modules,
    log_event,
    ensure_default_modules,
)
from app.models import ModuleRegistry
from app.modules.daily_digest import compute as daily_digest_compute
from app.modules.strong_events_alerts import compute as alerts_compute

# тип атома совместим с прежними тестами/модулями
Atom = Dict[str, object]

# карта доступных модулей: имя из таблицы module_registry -> функция compute(user_id) -> List[Atom]
MODULES = {
    "daily_digest": daily_digest_compute,
    "strong_events_alerts": alerts_compute,
}


def rank_atoms(atoms: List[Atom]) -> List[Atom]:
    """Сортируем по weight по убыванию (дефолт = 1)."""
    return sorted(atoms, key=lambda a: a.get("weight", 1), reverse=True)


def render_text(atoms: List[Atom]) -> str:
    return "\n".join(str(a.get("text", "")) for a in atoms)


def compute_atoms(user_id: str) -> List[Atom]:
    """Читаем включённые модули из БД и собираем атомы."""

    with session_scope() as db:
        enabled = list_enabled_modules(db)
        enabled_modules = [m.module for m in enabled]

    # 1) Фолбэк на пустую БД/отсутствие сидов
    if not enabled_modules:
        enabled_modules = list(MODULES.keys())

    atoms: List[Atom] = []
    for name in enabled_modules:
        fn = MODULES.get(name)
        if not fn:
            continue
        try:
            result = fn(user_id)  # каждая compute возвращает List[Atom]
            if result:
                atoms.extend(result)
        except Exception:
            # не даём упасть всему конвейеру из-за одного модуля
            continue

    # 2) Жёсткий предохранитель: даже если модули молчат или упали, вернём 1 атом
    if not atoms:
        atoms = [{"kind": "headline", "text": "Your stars today"}]

    return rank_atoms(atoms)


def run_preview(user_id: str) -> dict:
    """Собираем атомы, гарантируем сид модулей и логируем событие."""

    # 0) Гарантируем сид модулей (первая попытка)
    with session_scope() as db:
        ensure_default_modules(db)

    # 1) Собираем атомы и текст
    atoms = compute_atoms(user_id)
    text = render_text(atoms)

    # 2) Читаем включённые модули НОВОЙ сессией.
    #    Если по какой-то причине пусто — дописываем ORM'ом и перечитываем.
    with session_scope() as db:
        rows = list_enabled_modules(db)
        if not rows:
            to_upsert: list[ModuleRegistry] = []
            names = {"daily_digest", "strong_events_alerts"}
            # чтобы не дублировать, проверим точечно
            existing = {m.module for m in db.query(ModuleRegistry).all()}
            for name in sorted(names - existing):
                to_upsert.append(ModuleRegistry(module=name, enabled=True, config={}))
            if to_upsert:
                db.add_all(to_upsert)
                db.commit()
            rows = list_enabled_modules(db)

        mod_names = [m.module for m in rows]  # ← именно из БД

    # 3) Логируем событие
    payload = {
        "user_id": user_id,
        "atoms": len(atoms),
        "text_len": len(text),
        "modules": mod_names,
    }
    with session_scope() as db:
        ev = log_event(
            db,
            event="preview_rendered",
            user_id=user_id,
            payload=payload,
        )

    # 4) Контракт ответа
    ts = datetime.utcnow().isoformat() + "Z"
    return {
        "ok": True,
        "ts": ts,
        "user_id": user_id,
        "modules": mod_names,  # ← гарантированно из БД
        "event_id": ev.id,
        "atoms": atoms,
        "text": text,
        "count": len(atoms),
        "event": {
            "user_id": user_id,
            "atoms": len(atoms),
            "text_len": len(text),
            "event_id": ev.id,
        },
    }
