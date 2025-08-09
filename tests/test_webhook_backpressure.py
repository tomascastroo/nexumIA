from fastapi.testclient import TestClient


def test_webhook_responds_quickly(monkeypatch):
    # Ensure app loads with known env
    monkeypatch.setenv("SECRET_KEY", "test_secret_key")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///./test.db")
    import sys
    sys.modules.pop("db.db", None)
    sys.modules.pop("main", None)
    from db.db import Base, engine
    Base.metadata.create_all(bind=engine)
    import main as mainmod
    client = TestClient(mainmod.app)

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

