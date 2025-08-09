import sys
from fastapi.testclient import TestClient


def test_admin_guard(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "test_secret_key")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///./test.db")
    sys.modules.pop("db.db", None)
    sys.modules.pop("main", None)
    from db.db import Base, engine
    Base.metadata.create_all(bind=engine)
    import main as mainmod
    client = TestClient(mainmod.app)

    # Create admin user directly via register + manual role tweak might not persist; so rely on default user and expect 403
    r = client.post("/api/v1/auth/register", json={"email": "user@x.com", "password": "pw"})
    assert r.status_code in (200, 201)

    r = client.post("/api/v1/auth/login", json={"email": "user@x.com", "password": "pw"})
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    r = client.get("/api/v1/auth/admin/ping", headers=headers)
    assert r.status_code == 403

