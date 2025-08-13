from app import app


def test_llm_health_endpoint(monkeypatch):
    # Ensure we use mock provider for tests
    monkeypatch.setenv("SC_PROFILE", "local")
    client = app.test_client()
    res = client.get("/api/health/llm")
    assert res.status_code == 200
    data = res.get_json()
    assert "ok" in data
