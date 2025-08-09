import pytest
from httpx import AsyncClient
from httpx import ASGITransport
import sys

def _load_app(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "test_secret_key")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///./test.db")
    monkeypatch.setenv("DISABLE_RATE_LIMITER", "true")
    sys.modules.pop("db.db", None)
    sys.modules.pop("main", None)
    from db.db import Base, engine
    Base.metadata.create_all(bind=engine)
    import main as mainmod
    return mainmod.app

@pytest.mark.asyncio
async def test_analyze_strategies_and_status(monkeypatch):
    app = _load_app(monkeypatch)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
    strategies = [{"id": 1, "name": "Estrategia 1"}, {"id": 2, "name": "Estrategia 2"}]
    # Ajuste: usar endpoint expuesto para pruebas IA (message router)
    resp = await ac.post("/debtors/analyze", json=strategies)
        assert resp.status_code == 200
        data = resp.json()
        assert "task_id" in data
        task_id = data["task_id"]
        # Consultar estado
        status_resp = await ac.get(f"/task_status/{task_id}")
        assert status_resp.status_code == 200
        assert status_resp.json()["task_id"] == task_id 