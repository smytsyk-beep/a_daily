# src/app/scripts/seed_content_atoms_v0.py

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from app.db import SessionLocal
from app import models


LOCALES: List[str] = ["en", "ru", "es"]
LOCALES_DIR = Path(__file__).resolve().parents[1] / "locales"


# Мета-описание day-атомов: без текстов, только структура и теги.
DAY_TOPICS: Dict[str, Dict[str, Any]] = {
    "day_general_balance": {
        "json_key": "general_balance",
        "style": "supportive",
        "persona_tags": ["general"],
        "house_tags": None,
        "strength_hint": "light_to_medium",
    },
    "day_general_selfcare": {
        "json_key": "general_selfcare",
        "style": "reflective",
        "persona_tags": ["general"],
        "house_tags": None,
        "strength_hint": "light_to_medium",
    },
    "day_work_focus": {
        "json_key": "work_focus",
        "style": "supportive",
        "persona_tags": ["general"],
        "house_tags": None,
        "strength_hint": "light_to_medium",
    },
    "day_money_focus": {
        "json_key": "money_focus",
        "style": "supportive",
        "persona_tags": ["general"],
        "house_tags": None,
        "strength_hint": "light_to_medium",
    },
    "day_love_vibes": {
        "json_key": "love_vibes",
        "style": "reflective",
        "persona_tags": ["general"],
        "house_tags": None,
        "strength_hint": "light_to_medium",
    },
    "day_selfcare_nervous_system": {
        "json_key": "selfcare_nervous_system",
        "style": "reflective",
        "persona_tags": ["general"],
        "house_tags": None,
        "strength_hint": "light_to_medium",
    },
}


def _load_locale_dict(locale: str) -> Dict[str, Any]:
    path = LOCALES_DIR / f"{locale}.json"
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _extract_texts(locale_dict: Dict[str, Any], json_key: str) -> Dict[str, str]:
    """
    Берём тексты для атома из locales/<locale>.json → atoms.day.<json_key>.
    Ожидаем 4 поля: body, copy_short, copy_long, cta.
    """
    try:
        node = locale_dict["atoms"]["day"][json_key]
    except KeyError as exc:
        raise KeyError(f"Missing atoms.day.{json_key} in locale JSON") from exc

    return {
        "body": node["body"],
        "copy_short": node["copy_short"],
        "copy_long": node["copy_long"],
        "cta": node["cta"],
    }


def _upsert_atom(
    db,
    locale: str,
    topic_tag: str,
    fields: Dict[str, Any],
) -> models.ContentAtom:
    """
    Простой upsert по паре (locale, topic_tag):
    - если атом уже есть — обновляем поля;
    - если нет — создаём новый.
    """
    atom = (
        db.query(models.ContentAtom)
        .filter(
            models.ContentAtom.locale == locale,
            models.ContentAtom.topic_tag == topic_tag,
        )
        .one_or_none()
    )

    if atom is not None:
        for k, v in fields.items():
            setattr(atom, k, v)
    else:
        atom = models.ContentAtom(
            locale=locale,
            topic_tag=topic_tag,
            **fields,
        )
        db.add(atom)

    return atom


def seed_content_atoms_v0() -> None:
    """
    Минимальный набор day-контента v0.

    Логика:
    - описываем структуру и теги атомов в DAY_TOPICS;
    - тексты храним в locales/<locale>.json → atoms.day.*;
    - здесь просто подтягиваем тексты и делаем upsert в content_atoms.
    """
    db = SessionLocal()
    total = 0

    try:
        # Кешируем JSON по локали
        locales_cache: Dict[str, Dict[str, Any]] = {
            loc: _load_locale_dict(loc) for loc in LOCALES
        }

        for locale in LOCALES:
            locale_dict = locales_cache[locale]
            for topic_tag, meta in DAY_TOPICS.items():
                json_key = meta["json_key"]
                texts = _extract_texts(locale_dict, json_key)

                fields: Dict[str, Any] = {
                    "style": meta["style"],
                    "persona_tags": meta["persona_tags"],
                    "house_tags": meta["house_tags"],
                    "strength_hint": meta["strength_hint"],
                    **texts,
                }

                _upsert_atom(
                    db=db,
                    locale=locale,
                    topic_tag=topic_tag,
                    fields=fields,
                )
                total += 1

        db.commit()
        print(f"Seeded/updated {total} content atoms (v0) from locale JSON.")
    finally:
        db.close()


if __name__ == "__main__":
    seed_content_atoms_v0()
