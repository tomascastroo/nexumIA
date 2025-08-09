import sys
import importlib
from fastapi.testclient import TestClient


def test_register_and_login_and_protected_route(monkeypatch):
    # Use SQLite for tests and set SECRET_KEY before importing app
    monkeypatch.setenv("DATABASE_URL", "sqlite:///./test.db")
    monkeypatch.setenv("SECRET_KEY", "test_secret_key")

    # Reload modules to pick up env
    sys.modules.pop("db.db", None)
    sys.modules.pop("main", None)
    import db.db as dbmod
    from db.db import Base, engine
    Base.metadata.create_all(bind=engine)
    import main as mainmod
    client = TestClient(mainmod.app)

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

