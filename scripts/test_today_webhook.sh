#!/bin/bash
# Скрипт для тестирования /today команды через curl

TG_USER_ID=${1:-6051740993}
API_URL=${2:-http://localhost:8080}

echo "============================================================"
echo "Simulating /today command for tg_user_id=$TG_USER_ID"
echo "API URL: $API_URL/telegram/webhook"
echo "============================================================"
echo

PAYLOAD=$(cat <<EOF
{
  "update_id": 123456789,
  "message": {
    "message_id": 1,
    "from": {
      "id": $TG_USER_ID,
      "is_bot": false,
      "first_name": "Test",
      "username": "testuser",
      "language_code": "ru"
    },
    "chat": {
      "id": $TG_USER_ID,
      "type": "private"
    },
    "date": $(date +%s),
    "text": "/today"
  }
}
EOF
)

curl -X POST "$API_URL/telegram/webhook" \
  -H "Content-Type: application/json" \
  -d "$PAYLOAD" \
  --max-time 30

echo
echo "============================================================"
echo
