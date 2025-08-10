import sys
import importlib
from fastapi.testclient import TestClient


def test_register_and_login_and_protected_route(monkeypatch):
    # Use SQLite for tests and set SECRET_KEY before importing app
    monkeypatch.setenv("DATABASE_URL", "sqlite:///./test.db")
    monkeypatch.setenv("SECRET_KEY", "test_secret_key")
    monkeypatch.setenv("DISABLE_RATE_LIMITER", "true")

    # Reload modules to pick up env
    sys.modules.pop("db.db", None)
    sys.modules.pop("main", None)
    import db.db as dbmod
    from db.db import Base, engine
    import models.User  # ensure users table is registered in metadata
    Base.metadata.create_all(bind=engine)
    import main as mainmod
    client = TestClient(mainmod.app)

    # Register with unique email
    import uuid
    unique_email = f"test_{uuid.uuid4().hex[:8]}@test.com"
    r = client.post("/api/v1/auth/register", json={"email": unique_email, "password": "x"})
    assert r.status_code in (200, 201)

    # Login
    r = client.post("/api/v1/auth/login", json={"email": unique_email, "password": "x"})
    assert r.status_code == 200
    token = r.json()["access_token"]

    # Call a protected endpoint that exists (whoami endpoint)
    headers = {"Authorization": f"Bearer {token}"}
    r = client.get("/api/v1/auth/whoami", headers=headers)
    # Should return 200 OK with user info
    assert r.status_code == 200

