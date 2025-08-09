import os
from fastapi.testclient import TestClient
from main import app


def test_register_and_login_and_protected_route(monkeypatch):
    # Ensure SECRET_KEY for tests
    monkeypatch.setenv("SECRET_KEY", "test_secret_key")

    client = TestClient(app)

    # Register
    r = client.post("/api/v1/auth/register", json={"email": "a@a.com", "password": "x"})
    assert r.status_code in (200, 201)

    # Login
    r = client.post("/api/v1/auth/login", json={"email": "a@a.com", "password": "x"})
    assert r.status_code == 200
    token = r.json()["access_token"]

    # Call a protected endpoint that exists (debtor list or similar)
    headers = {"Authorization": f"Bearer {token}"}
    r = client.get("/api/v1/debtor", headers=headers)
    # Accept 200 OK or 404/empty depending on dataset, but not unauthorized
    assert r.status_code in (200, 404)

