# src/app/orchestrator.py

from datetime import datetime
from typing import List, Dict, Union

from sqlalchemy.orm import Session

from app.repo import (
    session_scope,
    list_enabled_modules,
    log_event,
    ensure_default_modules,
    get_content_atom,
    DEFAULT_LOCALE,
)
from app.models import ModuleRegistry, User
from app.modules.daily_digest import compute as daily_digest_compute
from app.modules.strong_events_alerts import compute as alerts_compute

# тип атома совместим с прежними тестами/модулями
Atom = Dict[str, object]

# карта доступных модулей: имя из таблицы module_registry -> функция compute(user_id) -> List[Atom]
MODULES = {
    "daily_digest": daily_digest_compute,
    "strong_events_alerts": alerts_compute,
}


def _get_user_locale(user_ref: str | int) -> str:
    """
    Возвращает locale пользователя по user_id или tg_user_id.
    Если пользователя нет или locale не задана — берём DEFAULT_LOCALE.
    """
    with session_scope() as db:
        # numeric id
        if isinstance(user_ref, int) or (
            isinstance(user_ref, str) and user_ref.isdigit()
        ):
            uid = int(user_ref)
            user = db.get(User, uid)
        else:
            alias = str(user_ref)
            user = db.query(User).filter(User.tg_user_id == alias).first()

        if not user or not user.locale:
            return DEFAULT_LOCALE

        return user.locale


def _resolve_atoms_texts(
    db: Session,
    atoms: List[Atom],
    locale: str,
) -> List[Atom]:
    """
    Для атомов без text, но с topic_tag, подтягиваем тело из ContentAtom
    с учётом locale (и фолбеком внутри get_content_atom).
    """
    resolved: List[Atom] = []

    for atom in atoms:
        # уже есть текст → ничего не делаем
        if atom.get("text"):
            resolved.append(atom)
            continue

        topic_tag = atom.get("topic_tag")
        if not topic_tag:
            resolved.append(atom)
            continue

        content_atom = get_content_atom(
            db=db,
            topic_tag=str(topic_tag),
            locale=locale,
        )
        if content_atom:
            # копия, чтобы не трогать оригинал, если он переиспользуется
            atom = dict(atom)
            atom.setdefault("text", content_atom.body)

        resolved.append(atom)

    return resolved


def rank_atoms(atoms: List[Atom]) -> List[Atom]:
    """Сортируем по weight по убыванию (дефолт = 1)."""
    return sorted(atoms, key=lambda a: a.get("weight", 1), reverse=True)


def render_text(atoms: List[Atom]) -> str:
    return "\n".join(str(a.get("text", "")) for a in atoms)


def compute_atoms(user_id: str) -> List[Atom]:
    """Читаем включённые модули из БД, считаем атомы и подставляем текст по локали."""

    # локаль пользователя (ru/en/es)
    user_locale = _get_user_locale(user_id)

    # 1) включённые модули
    with session_scope() as db:
        enabled = list_enabled_modules(db)
        enabled_modules = [m.module for m in enabled]

    # фолбек на пустую БД/отсутствие сидов
    if not enabled_modules:
        enabled_modules = list(MODULES.keys())

    atoms: List[Atom] = [
        {
            "module": "orchestrator",
            "kind": "headline",
            "text": "Your stars today",
            "weight": 0,
        }
    ]

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

    # 2) Подставляем текст из ContentAtom, если его ещё нет
    with session_scope() as db:
        for atom in atoms:
            # если текст уже есть, ничего не делаем (для совместимости со старыми модулями)
            if atom.get("text"):
                continue

            topic_tag = atom.get("topic_tag")
            if not topic_tag:
                continue

            ca = get_content_atom(
                db=db,
                topic_tag=str(topic_tag),
                locale=user_locale,
                fallback_locale=DEFAULT_LOCALE,
            )
            if ca:
                atom["text"] = ca.body
            else:
                # грубый фолбек: хотя бы что-то осмысленное
                atom["text"] = str(topic_tag)

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
