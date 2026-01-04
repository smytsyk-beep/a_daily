# src/app/pdf_daily.py

from __future__ import annotations

"""
Простейший stub-сервис для PDF-версии daily-дайджеста.

Задача этого модуля сейчас:
- принять заголовок, тело и аффирмацию;
- собрать человекочитаемый текст;
- вернуть bytes, которые мы будем трактовать как «PDF-контент».

Важно: это *заглушка*. В следующих шагах можно будет подключить
нормальный PDF-рендерер (WeasyPrint / ReportLab / wkhtmltopdf и т.п.)
и сохранить такой же интерфейс функции.
"""


def build_daily_digest_pdf(
    *,
    title: str,
    body: str,
    affirmation: str | None = None,
    locale: str = "en",
) -> bytes:
    """
    Собирает текстовую версию дайджеста и возвращает bytes.

    Сейчас это НЕ настоящий PDF, а просто UTF-8 текст. Мы сознательно
    делаем минимальный stub, чтобы:
    - иметь единый интерфейс для будущего реального PDF;
    - можно было уже сейчас покрыть это тестом и навесить план-/feature-гейтинг.

    :param title: заголовок дайджеста
    :param body: основной текст
    :param affirmation: доп. аффирмация (опционально)
    :param locale: текущий язык (пока не используется, но пригодится позже)
    :return: bytes, условно представляющие PDF-файл
    """
    lines: list[str] = []

    lines.append("AstroDaily — Daily Digest")
    lines.append(f"Locale: {locale}")
    lines.append("")
    lines.append(f"Title: {title}")
    lines.append("")
    lines.append(body)

    if affirmation:
        lines.append("")
        lines.append("Affirmation:")
        lines.append(affirmation)

    # В будущем вместо этого блока будет настоящий PDF-рендеринг.
    text = "\n".join(lines)
    return text.encode("utf-8")
