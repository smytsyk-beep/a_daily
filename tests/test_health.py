from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    d = r.json()
    assert d.get("ok") is True
    assert "version" in d
