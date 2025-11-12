from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_post_feedback_ok():
    # сначала убедимся, что превью рендерится (создаст пользователя и базовый ивент)
    _ = client.get("/orchestrator/preview?user_id=demo")

    r = client.post("/events/feedback", json={"user_id":"demo","score":5,"note":"looks good"})
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True
    assert isinstance(data["event_id"], int)