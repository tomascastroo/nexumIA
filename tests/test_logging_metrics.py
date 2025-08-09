from fastapi.testclient import TestClient
import sys


def test_metrics_endpoint(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "test_secret_key")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///./test.db")
    monkeypatch.setenv("DISABLE_RATE_LIMITER", "true")
    sys.modules.pop("db.db", None)
    sys.modules.pop("main", None)
    from db.db import Base, engine
    Base.metadata.create_all(bind=engine)
    import main as mainmod
    client = TestClient(mainmod.app)
    r = client.get("/metrics")
    # FastAPI router returns the Prometheus metrics response
    assert r.status_code == 200
    assert "python_info" in r.text or "http_requests_total" in r.text

