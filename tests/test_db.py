from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_db_health():
    r = client.get("/db/health")
    assert r.status_code == 200
    assert r.json().get("ok") is True
