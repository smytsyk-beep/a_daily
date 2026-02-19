#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Проверка наличия контент-атомов для всех локалей (EN/ES/RU) и всех интересов.

Интересы: work, relationships, money, selfcare, learning, creativity (+ general).
Для «тихого дня» нужны topic_tag: day_general_balance, day_general_selfcare,
day_work_focus, day_money_focus, day_love_vibes, day_selfcare_nervous_system.

Запуск: из корня проекта
  docker compose exec app python scripts/check_atoms_interests_locales.py
  или: PYTHONPATH=src python scripts/check_atoms_interests_locales.py
"""

from __future__ import annotations

import sys
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from app.repo import session_scope
from app import models

LOCALES = ["en", "ru", "es"]
INTERESTS = [
    "work",
    "relationships",
    "money",
    "selfcare",
    "learning",
    "creativity",
    "general",
]
# relationships в сидах часто как "love" — считаем оба
INTEREST_ALIASES = {"relationships": ["relationships", "love"]}
DAY_TOPIC_TAGS = [
    "day_general_balance",
    "day_general_selfcare",
    "day_work_focus",
    "day_money_focus",
    "day_love_vibes",
    "day_selfcare_nervous_system",
]


def normalize_persona(tags: list | None) -> set[str]:
    if not tags:
        return set()
    return {str(t).strip().lower() for t in tags if str(t).strip()}


def main() -> None:
    print("=" * 80)
    print("ATOMS BY LOCALE AND INTEREST (persona_tags)")
    print("=" * 80)

    with session_scope() as db:
        # 1) Day atoms: по topic_tag и locale
        print("\n1) DAY ATOMS (topic_tag) — для тихого дня / select_general_day_atoms")
        print("-" * 60)
        for locale in LOCALES:
            row = (
                db.query(models.ContentAtom)
                .filter(
                    models.ContentAtom.locale == locale,
                    models.ContentAtom.topic_tag.in_(DAY_TOPIC_TAGS),
                )
                .all()
            )
            by_topic = defaultdict(int)
            for a in row:
                by_topic[a.topic_tag or "null"] += 1
            missing = set(DAY_TOPIC_TAGS) - set(by_topic.keys())
            status = "OK" if not missing else f"MISSING: {sorted(missing)}"
            print(
                f"  {locale.upper():3}  total={len(row):3}  by topic: {dict(by_topic)}  {status}"
            )

        # 2) Persona_tags coverage per locale
        print(
            "\n2) ATOMS WITH PERSONA_TAGS (transit/general) — для ранжирования по интересам"
        )
        print("-" * 60)
        for locale in LOCALES:
            atoms = (
                db.query(models.ContentAtom)
                .filter(
                    models.ContentAtom.locale == locale,
                )
                .all()
            )
            has_tag = defaultdict(int)
            for a in atoms:
                tags = normalize_persona(a.persona_tags)
                if not tags:
                    has_tag["(no tags)"] += 1
                    continue
                for t in tags:
                    has_tag[t] += 1
            # интересы: work, relationships/love, money, selfcare, learning, creativity, general
            interest_ok = []
            interest_miss = []
            for i in INTERESTS:
                if i == "relationships":
                    count = has_tag.get("relationships", 0) + has_tag.get("love", 0)
                else:
                    count = has_tag.get(i, 0)
                if count > 0:
                    interest_ok.append(i)
                else:
                    interest_miss.append(i)
            print(
                f"  {locale.upper():3}  total atoms={len(atoms)}  with persona: {dict(has_tag)}"
            )
            print(f"       interests covered: {interest_ok}")
            if interest_miss:
                print(f"       MISSING persona_tags for: {interest_miss}")

        # 3) Краткая сводка: есть ли хотя бы один атом с каждым интересом по локалям
        print("\n3) SUMMARY — минимум 1 атом с данным persona_tag по локалям")
        print("-" * 60)
        matrix = []
        for interest in INTERESTS:
            row = []
            for locale in LOCALES:
                if interest == "relationships":
                    q = (
                        db.query(models.ContentAtom)
                        .filter(
                            models.ContentAtom.locale == locale,
                        )
                        .all()
                    )
                    count = sum(
                        1
                        for a in q
                        if (
                            normalize_persona(a.persona_tags)
                            & {"relationships", "love"}
                        )
                    )
                else:
                    q = (
                        db.query(models.ContentAtom)
                        .filter(
                            models.ContentAtom.locale == locale,
                        )
                        .all()
                    )
                    count = sum(
                        1 for a in q if interest in normalize_persona(a.persona_tags)
                    )
                row.append(count)
            matrix.append((interest, row))
        print(f"  {'Interest':20}  EN    RU    ES")
        for interest, row in matrix:
            cells = "  ".join(f"{n:5}" for n in row)
            ok = "OK" if all(n > 0 for n in row) else "GAP"
            print(f"  {interest:20}  {cells}  {ok}")

    print("\n" + "=" * 80)
    print("Done. GAP = хотя бы одна локаль без атомов с этим тегом.")
    print("=" * 80)


if __name__ == "__main__":
    main()


# -----------------------------------------------------------------------------
# ОТЧЁТ ПО СИДАМ (без БД) — что есть в коде/сидах для EN/ES/RU и интересов
# -----------------------------------------------------------------------------
#
# 1) DAY ATOMS (topic_tag для тихого дня)
#    RU: seed_atoms_ru_daily_and_special.py — все 6 topic_tag (day_general_balance,
#        day_general_selfcare, day_work_focus, day_money_focus, day_love_vibes,
#        day_selfcare_nervous_system), с persona_tags.
#    EN: seed_content_atoms_v0.py + locales/en.json (atoms.day.*) — все 6 topic_tag.
#    ES: seed_content_atoms_v0.py ожидает locales/es.json → atoms.day.*, но в es.json
#        секции atoms.day нет → день-атомы для ES могут отсутствовать. Добавить в es.json
#        структуру atoms.day (general_balance, work_focus, money_focus, love_vibes,
#        selfcare_nervous_system, general_selfcare) и перезапустить сид.
#
# 2) PERSONA_TAGS по локалям (транзиты, ретрограды, ингрессии, луна)
#    general — везде (EN/ES/RU).
#    work     — EN, RU, ES (много триггеров).
#    love     — EN, RU, ES (в сидах "love", не "relationships"; в RAG добавлен маппинг
#               interests "relationships" → query persona "love" + "relationships").
#    money    — EN, RU, ES (часть транзитов/ингрессов).
#    selfcare — EN, RU, ES.
#    learning — EN (retrograde Jupiter, house Jupiter 9h), RU (batch2, retrograde),
#               ES (retrograde Jupiter, house Jupiter 9h). Для транзитов по триггерам
#               типа uranus_jupiter — learning есть не у всех триггеров.
#    creativity — RU (seed_transit_atoms_ru_es: mercury_venus_flow, sun_uranus_freedom),
#                 ES (sun_uranus_freedom). EN — проверить по БД (в seed_transit_atoms_en
#                 в основном general/work/selfcare/love).
#
# 3) Рекомендации
#    - Запустить скрипт в контейнере: docker compose exec app python scripts/check_atoms_interests_locales.py
#    - Добавить в es.json секцию atoms.day для днятомов ES.
#    - При необходимости добавить атомы с persona_tags learning/creativity для частых
#      транзитных триггеров (mars_square_sun, uranus_trine_jupiter и т.д.) во всех трёх локалях.
