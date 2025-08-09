from fastapi.testclient import TestClient
from main import app


def test_webhook_responds_quickly(monkeypatch):
    client = TestClient(app)

    # Monkeypatch Celery task to avoid real queue
    class DummyAsyncResult:
        id = "task123"
    class DummyTask:
        def delay(self, *args, **kwargs):
            return DummyAsyncResult()

    import routers.webhook as webhook_router
    webhook_router.process_incoming_message = DummyTask()

    data = {
        "From": "whatsapp:+5491100000000",
        "Body": "hola"
    }
    r = client.post("/webhook/", data=data)
    assert r.status_code == 200
    # Twilio XML minimal response
    assert "Gracias, procesaremos tu mensaje." in r.text

