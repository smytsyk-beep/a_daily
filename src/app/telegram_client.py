# src/app/telegram_client.py
from __future__ import annotations

import httpx

from common.config import settings


class TelegramClientError(Exception):
    pass


def _get_base_url() -> str:
    # ВАЖНО: имя поля такое же, как в Settings
    token = settings.TELEGRAM_BOT_TOKEN
    if not token:
        raise TelegramClientError("TELEGRAM_BOT_TOKEN is not configured")
    return f"https://api.telegram.org/bot{token}"


def send_message(
    chat_id: int,
    text: str,
    *,
    parse_mode: str | None = None,
    reply_markup: dict | None = None,
) -> None:
    """
    Отправка сообщения через Telegram Bot API.

    reply_markup позволяет передавать inline-кнопки.
    """
    base_url = _get_base_url()
    url = f"{base_url}/sendMessage"

    payload: dict = {
        "chat_id": chat_id,
        "text": text,
    }
    if parse_mode:
        payload["parse_mode"] = parse_mode
    if reply_markup:
        payload["reply_markup"] = reply_markup

    with httpx.Client(timeout=5.0) as client:
        resp = client.post(url, json=payload)
        if resp.status_code != 200:
            raise TelegramClientError(
                f"Telegram sendMessage failed: {resp.status_code} {resp.text}"
            )


def answer_callback_query(
    callback_query_id: str,
    *,
    text: str | None = None,
    show_alert: bool = False,
) -> None:
    """
    Подтверждает обработку callback query.
    
    Обязательно вызывать после обработки callback_data,
    иначе Telegram будет повторно отправлять callback_query.
    
    Args:
        callback_query_id: ID callback query из update
        text: Опциональный текст для показа пользователю (toast/alert)
        show_alert: Если True, показывает alert вместо toast
    """
    base_url = _get_base_url()
    url = f"{base_url}/answerCallbackQuery"

    payload: dict = {
        "callback_query_id": callback_query_id,
    }
    if text:
        payload["text"] = text
    if show_alert:
        payload["show_alert"] = True

    with httpx.Client(timeout=5.0) as client:
        resp = client.post(url, json=payload)
        if resp.status_code != 200:
            raise TelegramClientError(
                f"Telegram answerCallbackQuery failed: {resp.status_code} {resp.text}"
            )
