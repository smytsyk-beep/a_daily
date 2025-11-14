from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_preview_ok():
    r = client.get("/orchestrator/preview?user_id=demo")
    assert r.status_code == 200
    data = r.json()
    assert data.get("ok") is True
    assert isinstance(data.get("atoms"), list)
    assert "text" in data
