from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_preview_creates_event():
    _ = client.get("/orchestrator/preview?user_id=test")
    r = client.get("/events/recent?limit=1")
    assert r.status_code == 200
    items = r.json()
    assert items and items[0]["event"] == "preview_rendered"
