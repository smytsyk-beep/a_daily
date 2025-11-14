# tests/test_calendar_headers.py
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_calendar_ics_content_type():
    r = client.get("/calendar.ics")
    assert r.status_code == 200
    ct = r.headers.get("content-type", "")
    assert ct.lower().startswith("text/calendar")
