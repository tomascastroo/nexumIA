from typing import Any, Dict
import sys
from fastapi.testclient import TestClient


def test_start_and_continue_conversation(monkeypatch):
    # Env para test
    monkeypatch.setenv("DATABASE_URL", "sqlite:///./test.db")
    monkeypatch.setenv("SECRET_KEY", "test_secret_key")
    monkeypatch.setenv("DISABLE_RATE_LIMITER", "true")

    # Reload DB and app
    sys.modules.pop("db.db", None)
    sys.modules.pop("main", None)
    from db.db import Base, engine, SessionLocal
    import models.Debtor  # ensure table is registered
    Base.metadata.create_all(bind=engine)

    # Crear un debtor dummy
    from models.Debtor import Debtor
    db = SessionLocal()
    debtor = Debtor(phone="5491100000000", conversation_history=[])
    db.add(debtor)
    db.commit()
    db.refresh(debtor)

    # Mock OpenAI classify
    import services.openai_service as oai
    def dummy_classify_state(text: str) -> str:
        return "VERDE"
    oai.classify_state = dummy_classify_state  # type: ignore

    # Probar start_conversation
    from services.conversation_service import start_conversation, continue_conversation, classify_state
    conv = start_conversation(bot_id=1, debtor_id=debtor.id, context={"greeting": "hola"})
    assert conv["conversation_id"] == str(debtor.id)

    # Probar continue_conversation
    update = continue_conversation(str(debtor.id), "hola")
    assert "response" in update

    # Probar classify_state
    state = classify_state("quiero pagar")
    assert state in {"VERDE", "AMARILLO", "ROJO", "GRIS"}

