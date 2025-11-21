# tests/test_calendar_endpoint.py
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_calendar_ics_endpoint_basic():
    # system — будет создан/разрешён через resolve_user_id
    resp = client.get(
        "/calendar.ics",
        params={
            "user_id": "system",
            "days": 3,
            "tz": "Europe/Berlin",
        },
    )

    assert resp.status_code == 200
    # content-type может иметь charset, поэтому startswith
    assert resp.headers["content-type"].startswith("text/calendar")

    body = resp.text
    assert "BEGIN:VCALENDAR" in body
    assert "END:VCALENDAR" in body
    assert "X-WR-TIMEZONE:Europe/Berlin" in body
