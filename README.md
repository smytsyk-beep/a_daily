# AstroDaily — Starter Repo (Docker + CI)

See Quickstart inside.

GET /orchestrator/preview?user_id=demo

PS D:\msn\a-project\a_daily> curl.exe "http://127.0.0.1:8080/orchestrator/preview?user_id=demo"

{"ok":true,"count":2,"atoms":[
    {"module":"strong_events_alerts","kind":"alert","weight":3,"text":"Окно сильных транзитов: ближайшие 3 дня(ей)."},
    {"module":"daily_digest","kind":"digest","weight":2,"text":"Daily digest at 08:00: день выглядит продуктивным."}
    ],
    "text":"Окно сильных транзитов: ближайшие 3 дня(ей).\nDaily digest at 08:00: день выглядит продуктивным.",
    "event":{"user_id":"demo","atoms":2,"text_len":95,"event_id":40}}

POST /events/feedback (PowerShell Invoke-RestMethod и bash curl)

PS D:\msn\a-project\a_daily> curl.exe -s -X POST "http://127.0.0.1:8080/events/feedback" `
>>   -H "Content-Type: application/json" `
>>   --data-raw "$json"
{"detail":[
    {"type":"json_invalid","loc":["body",1],"msg":"JSON decode error","input":{},"ctx":{"error":"Expecting property name enclosed in double quotes"}}]}

*docker compose up -d

*alembic upgrade head

проверка:

**curl 127.0.0.1:8080/health

**curl "127.0.0.1:8080/orchestrator/preview?user_id=demo"

Added: /digest/daily, /alerts/strong, /calendar.ics, /orchestrator/preview

Infra: Alembic миграции, ensure_default_modules() (идемпотентный сид), стабилизация CI

Contracts: событие preview_rendered, поле atoms, верхнеуровневый text, event_id

Tests: 17 тестов (контракты, флаги фич, сиды)

**POST feedback (PowerShell):

Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8080/events/feedback" `
  -ContentType "application/json" -Body '{"user_id":"demo","score":4,"note":"nice"}'

Added: /digest/daily, /alerts/strong, /calendar.ics, /orchestrator/preview

Infra: Alembic миграции, ensure_default_modules() (идемпотентный сид), стабилизация CI

Contracts: событие preview_rendered, поле atoms, верхнеуровневый text, event_id

Tests: 17 тестов (контракты, флаги фич, сиды)
