import types


def test_whatsapp_env_usage(monkeypatch):
    monkeypatch.setenv("TWILIO_ACCOUNT_SID", "sid")
    monkeypatch.setenv("TWILIO_AUTH_TOKEN", "token")
    monkeypatch.setenv("TWILIO_WHATSAPP_NUMBER", "whatsapp:+14155238886")

    # Patch twilio Client to avoid real network
    class DummyClient:
        class messages:
            @staticmethod
            def create(body, from_, to):
                return types.SimpleNamespace(sid="fake_sid")

    import importlib, services.whatsapp_service as ws
    importlib.reload(ws)
    ws._client = DummyClient()

    sid = ws.send_whatsapp_message("whatsapp:+5491100000000", "hola")
    assert sid == "fake_sid"

