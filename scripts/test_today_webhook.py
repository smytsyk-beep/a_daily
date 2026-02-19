#!/usr/bin/env python3
"""
Скрипт для тестирования /today через эмуляцию Telegram webhook.

Usage:
    python scripts/test_today_webhook.py --user-id 1888
"""
import argparse
import json
import requests
from datetime import datetime


def simulate_today_command(tg_user_id: int, api_url: str = "http://localhost:8080"):
    """
    Симулирует отправку команды /today через Telegram webhook.
    """
    # Формируем payload, имитирующий Telegram update
    update_payload = {
        "update_id": 123456789,
        "message": {
            "message_id": 1,
            "from": {
                "id": tg_user_id,
                "is_bot": False,
                "first_name": "Test",
                "username": "testuser",
                "language_code": "ru",
            },
            "chat": {"id": tg_user_id, "type": "private"},
            "date": int(datetime.utcnow().timestamp()),
            "text": "/today",
        },
    }

    print(f"\n{'=' * 60}")
    print(f"Simulating /today command for tg_user_id={tg_user_id}")
    print(f"API URL: {api_url}/telegram/webhook")
    print(f"{'=' * 60}\n")

    try:
        response = requests.post(
            f"{api_url}/telegram/webhook",
            json=update_payload,
            headers={"Content-Type": "application/json"},
            timeout=30,
        )

        print(f"Response Status: {response.status_code}")
        print(f"Response Body:")
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))

        if response.status_code == 200:
            print("\n✅ Request successful!")
        else:
            print(f"\n❌ Request failed with status {response.status_code}")

    except requests.exceptions.Timeout:
        print("\n❌ Request timed out (>30s)")
    except requests.exceptions.ConnectionError as e:
        print(f"\n❌ Connection error: {e}")
        print(
            "\nHint: Make sure the app container is running (docker ps | grep astrodaily_app)"
        )
    except Exception as e:
        print(f"\n❌ Error: {e}")

    print(f"\n{'=' * 60}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Test /today webhook for AstroDaily Telegram bot"
    )
    parser.add_argument(
        "--user-id",
        type=int,
        required=True,
        help="Telegram user ID (tg_user_id) to test",
    )
    parser.add_argument(
        "--api-url",
        type=str,
        default="http://localhost:8080",
        help="API base URL (default: http://localhost:8080)",
    )

    args = parser.parse_args()

    simulate_today_command(args.user_id, args.api_url)


if __name__ == "__main__":
    main()
