import pytest
from httpx import AsyncClient
from main import app

@pytest.mark.asyncio
async def test_analyze_strategies_and_status():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        strategies = [{"id": 1, "name": "Estrategia 1"}, {"id": 2, "name": "Estrategia 2"}]
        resp = await ac.post("/strategies/analyze", json=strategies)
        assert resp.status_code == 200
        data = resp.json()
        assert "task_id" in data
        task_id = data["task_id"]
        # Consultar estado
        status_resp = await ac.get(f"/task_status/{task_id}")
        assert status_resp.status_code == 200
        assert status_resp.json()["task_id"] == task_id 