import pytest
from httpx import AsyncClient
from main import app

@pytest.mark.asyncio
async def test_send_whatsapp_and_status():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # Enviar mensaje WhatsApp
        payload = {"to": "+5491112345678", "message": "Hola!"}
        resp = await ac.post("/whatsapp/send", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert "task_id" in data
        task_id = data["task_id"]

        # Consultar estado de la tarea
        status_resp = await ac.get(f"/task_status/{task_id}")
        assert status_resp.status_code == 200
        status_data = status_resp.json()
        assert status_data["task_id"] == task_id
        assert status_data["status"] in ["PENDING", "STARTED", "SUCCESS", "FAILURE"] 