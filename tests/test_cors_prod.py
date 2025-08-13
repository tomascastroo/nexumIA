import pytest
from fastapi.testclient import TestClient
from main import app

@pytest.fixture(autouse=True)
def set_prod_env(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("ALLOWED_ORIGINS", "https://app.midominio.com")

def test_cors_rejects_unallowed_origin():
    client = TestClient(app)
    resp = client.get("/", headers={"Origin": "https://evil.com"})
    assert resp.headers.get("access-control-allow-origin") != "https://evil.com"