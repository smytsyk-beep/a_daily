#!/usr/bin/env python3
"""
Скрипт для тестирования /today через эмуляцию Telegram webhook (без внешних зависимостей).
"""
import sys
import json
import time
from http.client import HTTPConnection
from datetime import datetime


def simulate_today_command(tg_user_id: int, host: str = "localhost", port: int = 8080):
    """Симулирует отправку команды /today через Telegram webhook."""
    
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
            "date": int(time.time()),
            "text": "/today",
        },
    }

    print(f"\n{'=' * 60}")
    print(f"Simulating /today command for tg_user_id={tg_user_id}")
    print(f"API: {host}:{port}/telegram/webhook")
    print(f"{'=' * 60}\n")

    try:
        conn = HTTPConnection(host, port, timeout=30)
        
        body = json.dumps(update_payload)
        headers = {"Content-Type": "application/json"}
        
        conn.request("POST", "/telegram/webhook", body, headers)
        
        response = conn.getresponse()
        response_body = response.read().decode('utf-8')
        
        print(f"Response Status: {response.status}")
        print(f"Response Body:")
        try:
            response_json = json.loads(response_body)
            print(json.dumps(response_json, indent=2, ensure_ascii=False))
        except:
            print(response_body)

        if response.status == 200:
            print("\n✅ Request successful!")
        else:
            print(f"\n❌ Request failed with status {response.status}")

        conn.close()

    except Exception as e:
        print(f"\n❌ Error: {e}")

    print(f"\n{'=' * 60}\n")


if __name__ == "__main__":
    tg_user_id = int(sys.argv[1]) if len(sys.argv) > 1 else 6051740993
    simulate_today_command(tg_user_id)
