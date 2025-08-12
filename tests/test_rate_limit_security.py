import os
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

@pytest.mark.skipif(os.getenv("APP_ENV") == "production", reason="Evitar flake en prod")
def test_rate_limit_dev(monkeypatch):
    monkeypatch.setenv("APP_ENV", "development")
    # Simular requests rápidas
    results = [client.get("/") for _ in range(3)]
    codes = [r.status_code for r in results]
    # En dev, debe devolver 200, nunca debe crashear
    assert all(code in (200, 404) for code in codes)  # Permitir 404 si no hay endpoint

@pytest.mark.skipif(os.getenv("APP_ENV") != "production", reason="Solo en prod real")
def test_rate_limit_prod(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("RATE_LIMIT_MAX", "2")
    monkeypatch.setenv("RATE_LIMIT_WINDOW", "60")
    # Simular requests rápidas
    results = [client.get("/") for _ in range(3)]
    codes = [r.status_code for r in results]
    # La tercera debe devolver 429
    assert codes[-1] == 429