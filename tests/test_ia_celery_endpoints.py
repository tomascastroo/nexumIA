import pytest
from httpx import AsyncClient
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
async def test_analyze_debtors_and_status(monkeypatch):
    app = _load_app(monkeypatch)
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # Simular análisis masivo de deudores
        debtors = [{"id": 1, "name": "Juan"}, {"id": 2, "name": "Ana"}]
        resp = await ac.post("/debtors/analyze?dataset_id=1", json=debtors)
        assert resp.status_code == 200
        data = resp.json()
        assert "task_id" in data
        task_id = data["task_id"]
        # Consultar estado
        status_resp = await ac.get(f"/task_status/{task_id}")
        assert status_resp.status_code == 200
        assert status_resp.json()["task_id"] == task_id

@pytest.mark.asyncio
async def test_save_conversation_and_status(monkeypatch):
    app = _load_app(monkeypatch)
    async with AsyncClient(app=app, base_url="http://test") as ac:
        conversation = {"user": "Juan", "message": "Hola IA"}
        resp = await ac.post("/debtors/conversation?dataset_id=1", json=conversation)
        assert resp.status_code == 200
        data = resp.json()
        assert "task_id" in data
        task_id = data["task_id"]
        # Consultar estado
        status_resp = await ac.get(f"/task_status/{task_id}")
        assert status_resp.status_code == 200
        assert status_resp.json()["task_id"] == task_id 