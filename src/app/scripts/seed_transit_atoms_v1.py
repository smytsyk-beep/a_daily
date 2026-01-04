# src/app/scripts/seed_transit_atoms_v1.py
from __future__ import annotations

from typing import List, Dict, Any

from app import models
from app.repo import session_scope


def _upsert_atom(db, fields: Dict[str, Any]) -> models.ContentAtom:
    """
    Идемпотентный upsert для ContentAtom.

    Ключ для уникальности:
      (locale, topic_tag, trigger)
    """
    locale = fields["locale"]
    topic_tag = fields["topic_tag"]
    trigger = fields.get("trigger")

    q = (
        db.query(models.ContentAtom)
        .filter(models.ContentAtom.locale == locale)
        .filter(models.ContentAtom.topic_tag == topic_tag)
    )
    if trigger is None:
        q = q.filter(models.ContentAtom.trigger.is_(None))
    else:
        q = q.filter(models.ContentAtom.trigger == trigger)

    atom = q.first()

    payload = {
        "style": fields.get("style"),
        "body": fields.get("body"),
        "copy_short": fields.get("copy_short"),
        "copy_long": fields.get("copy_long"),
        "cta": fields.get("cta"),
        "trigger": trigger,
        "house_tags": fields.get("house_tags") or [],
        "persona_tags": fields.get("persona_tags") or [],
        "strength_hint": fields.get("strength_hint"),
    }

    if atom:
        # обновляем существующую запись
        for k, v in payload.items():
            setattr(atom, k, v)
    else:
        atom = models.ContentAtom(
            locale=locale,
            topic_tag=topic_tag,
            **payload,
        )
        db.add(atom)

    return atom


def seed_transit_atoms_v1() -> None:
    """
    Первые транзитные атомы:

    1) venus_trine_moon  — мягкая эмоциональная поддержка / отношения / selfcare
    2) mars_square_sun   — напряжение + шанс на конструктивный рывок
    """

    atoms: List[Dict[str, Any]] = [
        # --------- Venus trine Moon: гармоничный день, отношения / selfcare ---------
        # EN
        {
            "locale": "en",
            "topic_tag": "tr_venus_moon_harmony",
            "trigger": "venus_trine_moon",
            "style": "supportive",
            "persona_tags": ["general", "love", "selfcare"],
            "house_tags": [],
            "strength_hint": "light_to_medium",
            "copy_short": (
                "Emotions and desires move in the same direction today. "
                "Good time for gentle conversations, small pleasures and self-care."
            ),
            "copy_long": None,
            "body": (
                "Today the emotional tone is softer than usual. Venus and the Moon are in a "
                "supportive dialogue, so your feelings and needs are more in sync. This is a "
                "good day to slow down, listen to yourself and to the people close to you.\n\n"
                "Focus on simple pleasures and low-pressure plans: a calm walk, cooking "
                "something tasty, meaningful but not heavy conversations. Try to avoid drama "
                "and emotional overreactions — the sky is on your side if you choose kindness "
                "and warmth.\n\n"
                "If you’ve been meaning to gently clarify something in a relationship, you can "
                "do it now in a calm, honest tone. The main thing is to stay respectful to both "
                "your own feelings and the feelings of the other person."
            ),
            "cta": None,
        },
        # RU
        {
            "locale": "ru",
            "topic_tag": "tr_venus_moon_harmony",
            "trigger": "venus_trine_moon",
            "style": "supportive",
            "persona_tags": ["general", "love", "selfcare"],
            "house_tags": [],
            "strength_hint": "light_to_medium",
            "copy_short": (
                "Эмоции и желания сегодня двигаются в одном направлении. "
                "Подходит для мягких разговоров, простых удовольствий и заботы о себе."
            ),
            "copy_long": None,
            "body": (
                "Сегодня эмоциональный фон мягче обычного. Венера и Луна образуют "
                "поддерживающий аспект, поэтому чувства и потребности легче согласовать "
                "между собой. Это хороший день, чтобы немного замедлиться, прислушаться к "
                "себе и к близким.\n\n"
                "Сделай ставку на простые удовольствия и планы без лишнего давления: "
                "спокойная прогулка, вкусная еда, тёплые, но не тяжёлые разговоры. По "
                "возможности избегай драм и резких эмоциональных реакций — небесная картинка "
                "поддерживает именно мягкость и доброжелательность.\n\n"
                "Если давно хотелось что-то спокойно прояснить в отношениях, можно сделать "
                "это сейчас, без претензий и ультиматумов. Главное — уважать и свои чувства, "
                "и чувства другого человека."
            ),
            "cta": None,
        },
        # ES
        {
            "locale": "es",
            "topic_tag": "tr_venus_moon_harmony",
            "trigger": "venus_trine_moon",
            "style": "supportive",
            "persona_tags": ["general", "love", "selfcare"],
            "house_tags": [],
            "strength_hint": "light_to_medium",
            "copy_short": (
                "Emociones y deseos van en la misma dirección. Buen día para hablar con calma, "
                "disfrutar de cosas simples y cuidarte un poco más."
            ),
            "copy_long": None,
            "body": (
                "Hoy el clima emocional es más suave de lo habitual. Venus y la Luna forman un "
                "aspecto armonioso, así que lo que sientes y lo que necesitas es más fácil de "
                "alinear. Es un buen día para bajar el ritmo, escucharte y prestar atención a "
                "las personas cercanas.\n\n"
                "Elige planes sencillos y sin presión: un paseo tranquilo, comida rica, "
                "conversaciones significativas pero ligeras. Intenta no alimentar dramas ni "
                "reacciones exageradas: el cielo favorece la amabilidad y el calor humano.\n\n"
                "Si querías aclarar algo en una relación, puedes hacerlo ahora con honestidad "
                "y sin reproches. Lo importante es respetar tanto tus sentimientos como los de "
                "la otra persona."
            ),
            "cta": None,
        },
        # --------- Mars square Sun: напряжение + шанс на конструктивный рывок ---------
        # EN
        {
            "locale": "en",
            "topic_tag": "tr_mars_sun_push",
            "trigger": "mars_square_sun",
            "style": "growth",
            "persona_tags": ["general", "work", "selfcare"],
            "house_tags": [],
            "strength_hint": "medium",
            "copy_short": (
                "Energy is higher but less patient. Good moment to tackle a concrete task, "
                "as long as you move step by step and don’t burn yourself out."
            ),
            "copy_long": None,
            "body": (
                "Today the sky gives an extra dose of energy and impatience at the same time. "
                "The Mars–Sun aspect highlights where you’ve outgrown old limits and would like "
                "to move faster. This can be a productive transit if you direct it into one or "
                "two specific tasks instead of fighting with everyone and everything.\n\n"
                "Choose a realistic goal for the day: finish an overdue task, clean up a messy "
                "corner of your life, or make a clear decision you’ve been postponing. Act "
                "decisively, but check in with your body: tension in shoulders, jaw or stomach "
                "— сигнал притормозить и сделать паузу.\n\n"
                "Старайся не уходить в конфликт ради конфликта. Если что-то раздражает, сначала "
                "сформулируй, чего ты на самом деле хочешь изменить, и только потом действуй."
            ),
            "cta": None,
        },
        # RU
        {
            "locale": "ru",
            "topic_tag": "tr_mars_sun_push",
            "trigger": "mars_square_sun",
            "style": "growth",
            "persona_tags": ["general", "work", "selfcare"],
            "house_tags": [],
            "strength_hint": "medium",
            "copy_short": (
                "Энергии больше, терпения меньше. Хороший момент, чтобы взяться за конкретную "
                "задачу — если двигаться по шагам и не выжимать себя до нуля."
            ),
            "copy_long": None,
            "body": (
                "Сегодня небо добавляет и силы, и внутреннего напряжения. Квадратура Марса и "
                "Солнца подсвечивает те сферы, где старые ограничения уже тесны и хочется "
                "резко ускориться. Транзит может быть очень продуктивным, если направить его в "
                "одно-две конкретные задачи, а не в перепалки и борьбу с миром.\n\n"
                "Выбери реалистичную цель дня: закрыть зависшую задачу, навести порядок в "
                "хаотичном участке жизни или наконец принять решение, которое откладывалось. "
                "Действуй решительно, но регулярно проверяй тело: зажатые плечи, челюсть или "
                "тяжесть в животе — сигнал сделать паузу и выдохнуть.\n\n"
                "По возможности не вступай в конфликты ради самих конфликтов. Если что-то "
                "сильно раздражает, сначала сформулируй, что именно ты хочешь изменить, и уже "
                "потом переходи к действиям."
            ),
            "cta": None,
        },
        # ES
        {
            "locale": "es",
            "topic_tag": "tr_mars_sun_push",
            "trigger": "mars_square_sun",
            "style": "growth",
            "persona_tags": ["general", "work", "selfcare"],
            "house_tags": [],
            "strength_hint": "medium",
            "copy_short": (
                "Hay más energía y menos paciencia. Buen momento para avanzar en una tarea "
                "concreta, si vas paso a paso y no te llevas al límite."
            ),
            "copy_long": None,
            "body": (
                "Hoy el cielo trae un extra de energía junto con cierta tensión. El aspecto "
                "Marte–Sol muestra dónde te quedan pequeñas las viejas limitaciones y quieres "
                "acelerar. Puede ser un tránsito muy productivo si lo diriges a una o dos "
                "tareas claras, en lugar de discutir con todo el mundo.\n\n"
                "Elige un objetivo realista para el día: terminar algo pendiente, ordenar un "
                "espacio caótico o tomar una decisión que vienes posponiendo. Actúa con firmeza, "
                "pero escucha tu cuerpo: tensión en hombros, mandíbula o estómago es una señal "
                "de que necesitas una pausa.\n\n"
                "Evita los conflictos por puro impulso. Si algo te molesta mucho, primero "
                "ponle nombre a lo que realmente quieres cambiar y luego actúa desde ahí."
            ),
            "cta": None,
        },
    ]

    with session_scope() as db:
        for f in atoms:
            _upsert_atom(db, f)
        db.commit()

    print(f"Seeded/updated {len(atoms)} transit content atoms.")


if __name__ == "__main__":
    seed_transit_atoms_v1()
