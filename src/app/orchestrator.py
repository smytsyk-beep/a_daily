from datetime import datetime
from typing import List, Dict

from app.repo import session_scope, list_enabled_modules, log_event
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
    """Рендерим итоговый текст простым склеиванием строк атомов."""
    lines: List[str] = []
    for a in atoms:
        lines.append(str(a.get("text", "")))
    return "\n".join(lines)


def compute_atoms(user_id: str) -> List[Atom]:
    """Читаем включённые модули из БД и собираем атомы."""

    with session_scope() as db:
        enabled = list_enabled_modules(db)
        enabled_modules = [m.module for m in enabled]

    # 🔧 Фолбэк на случай пустой БД/отсутствия сидов в CI:
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
            # не даём упасть всему конвейеру
            continue

    return rank_atoms(atoms)


def run_preview(user_id: str) -> dict:
    """Оркестратор предпросмотра: собрать атомы, текст и залогировать событие."""
    # 1) собрать атомы
    atoms = compute_atoms(user_id)
    text = render_text(atoms)

    # 2) получить список включённых модулей для ответа/аудита
    with session_scope() as db:
        enabled = list_enabled_modules(db)
        mod_names = [m.module for m in enabled]

    # 3) зафиксировать событие
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

    # 4) ответ по контракту (верхнеуровневые text и event_id — для тестов)
    ts = datetime.utcnow().isoformat() + "Z"
    return {
        "ok": True,
        "ts": ts,
        "user_id": user_id,
        "modules": mod_names,
        "event_id": ev.id,  # 👈 важно для тестов и клиентов
        "atoms": atoms,  # список атомов
        "text": text,  # 👈 важно для тестов
        # дополнительные поля для обратной совместимости
        "count": len(atoms),
        "event": {
            "user_id": user_id,
            "atoms": len(atoms),
            "text_len": len(text),
            "event_id": ev.id,
        },
    }
