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
    enabled_modules: List[str]
    with session_scope() as db:
        enabled = list_enabled_modules(db)
        enabled_modules = [m.module for m in enabled]  # m.module — колонка из ModuleRegistry

    atoms: List[Atom] = []
    for name in enabled_modules:
        fn = MODULES.get(name)
        if not fn:
            # модуль есть в таблице, но нет в коде — пропускаем
            continue
        try:
            result = fn(user_id)  # каждая compute возвращает List[Atom]
            if result:
                atoms.extend(result)
        except Exception:
            # защищаемся от падения всего пайплайна из-за одного модуля
            continue

    return rank_atoms(atoms)


def run_preview(user_id: str):
    """Оркестратор предпросмотра: собрать атомы, текст и залогировать событие."""
    atoms = compute_atoms(user_id)
    text = render_text(atoms)
    payload = {"user_id": user_id, "atoms": len(atoms), "text_len": len(text)}

    # записываем событие в events_feedback (через корректный контекст-менеджер)
    with session_scope() as db:
        ev = log_event(
            db,
            event="preview_rendered",
            user_id=user_id,
            payload=payload,
        )

    return {
        "ok": True,
        "count": len(atoms),
        "atoms": atoms,
        "text": text,
        "event": {"user_id": user_id, "atoms": len(atoms), "text_len": len(text), "event_id": ev.id},
    }


"""
from typing import List, Dict
from app.repo import get_session, list_enabled_modules, log_event
from app.modules.daily_digest import compute as daily_digest_compute
from app.modules.strong_events_alerts import compute as alerts_compute

Atom = Dict[str, object]

MODULES = {
    "daily_digest": daily_digest_compute,
    "strong_events_alerts": alerts_compute,
}

def compute_atoms(user_id: str) -> List[Atom]:
    atoms: List[Atom] = []
    with get_session() as db:
        enabled = list_enabled_modules(db)
        for row in enabled:
            fn = MODULES.get(row.module)
            if not fn:
                continue
            cfg = row.config or {}
            atoms.extend(fn(user_id=user_id, config=cfg))
    return atoms

def rank_atoms(atoms: List[Atom]) -> List[Atom]:
    return sorted(atoms, key=lambda a: a.get("weight", 1), reverse=True)

def render_text(atoms: List[Atom]) -> str:
    lines = []
    for a in atoms:
        lines.append(str(a.get("text", "")))
    return "\n".join(lines)

def run_preview(user_id: str) -> Dict[str, object]:
    atoms = compute_atoms(user_id)
    ranked = rank_atoms(atoms)
    text = render_text(ranked[:10])
    payload = {"user_id": user_id, "atoms": len(ranked), "text_len": len(text)}
    
    with get_session() as db:
        ev = log_event(db, event="preview_rendered", user_id=user_id, payload=payload)  # <-- добавили user_id
        payload["event_id"] = ev.id

    return {"ok": True, "count": len(ranked), "atoms": ranked, "text": text, "event": payload}
"""