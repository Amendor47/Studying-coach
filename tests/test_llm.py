import os
from app import app


def test_health_llm_endpoint():
    os.environ["SC_PROFILE"] = "local"
    with app.test_client() as c:
        resp = c.get("/api/health/llm")
        data = resp.get_json()
        assert resp.status_code == 200
        assert data["provider"] == "mock"
        assert data["ok"] is True
