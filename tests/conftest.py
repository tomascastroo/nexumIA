import base64
import os
import pytest


@pytest.fixture(autouse=True)
def test_env(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "test_secret_key")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///./test.db")
    monkeypatch.setenv("DISABLE_RATE_LIMITER", "true")
    # Fernet key debe ser 32 bytes base64 urlsafe
    key = base64.urlsafe_b64encode(b"0" * 32).decode()
    monkeypatch.setenv("ENCRYPTION_KEY", key)
    yield
