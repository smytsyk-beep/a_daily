from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_daily_digest_contract():
    r = client.get("/digest/daily")
    assert r.status_code == 200
    js = r.json()
    assert "date" in js and "events" in js
    assert isinstance(js["events"], list)


def test_strong_alerts_contract():
    r = client.get("/alerts/strong")
    assert r.status_code == 200
    js = r.json()
    assert {"ts", "count", "events"} <= set(js.keys())


def test_calendar_ics_contract():
    r = client.get("/calendar.ics")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/calendar")
    assert "BEGIN:VCALENDAR" in r.text
