# 📂 Ruta: services/conversation_service.py
# 🔗 Abrir archivo: file://./services/conversation_service.py

from sqlalchemy.orm import Session
from typing import Any, Dict, Optional, List
from db.db import SessionLocal
from models.Debtor import Debtor
from schemas.conversation import Conversation, ConversationUpdate
from tasks.ia_tasks import process_incoming_message


def start_conversation(bot_id: int, debtor_id: int, context: Optional[Dict[str, Any]] = None) -> Conversation:
    """Inicializa una conversación para un deudor y retorna su estado y el historial inicial."""
    db: Session = SessionLocal()
    try:
        debtor = db.query(Debtor).filter(Debtor.id == debtor_id).first()
        if not debtor:
            raise ValueError("Debtor no encontrado")
        history: List[Dict[str, str]] = []
        if context:
            history.append({"role": "system", "content": str(context)})
        debtor.conversation_history = history
        db.commit()
        return Conversation(conversation_id=str(debtor_id), history=history, state=debtor.state)
    finally:
        db.close()


def continue_conversation(conversation_id: str, message: str) -> ConversationUpdate:
    """Continúa una conversación existente, añade el mensaje y delega la respuesta a la tarea asíncrona."""
    db: Session = SessionLocal()
    try:
        phone: Optional[str] = None
        debtor: Optional[Debtor] = None
        if conversation_id.isdigit():
            debtor = db.query(Debtor).filter(Debtor.id == int(conversation_id)).first()
            if debtor and debtor.phone:
                phone = str(debtor.phone)
        else:
            phone = conversation_id
            debtor = db.query(Debtor).filter(Debtor.phone == phone).first()
        if not debtor or not phone:
            raise ValueError("Conversación no encontrada para conversation_id")

        # Encolar la tarea asíncrona y esperar el resultado (en producción, esto podría ser polling o un callback)
        result = process_incoming_message.apply(args=[phone, message])
        response_text = result.get(timeout=10)  # Espera hasta 10s por la respuesta
        # Recargar historial y estado actualizado
        updated_debtor = db.query(Debtor).filter(Debtor.id == debtor.id).first()
        history = updated_debtor.conversation_history if updated_debtor else []
        state = updated_debtor.state if updated_debtor else None
        return ConversationUpdate(conversation_id=conversation_id, response=response_text.get("response", ""), history=history, state=state)
    finally:
        db.close()


def classify_state(text: str) -> str:
    """Clasifica estado usando OpenAI a través del servicio unificado."""
    from services.openai_service import classify_state as oai_classify_state
    try:
        return oai_classify_state(text)
    except Exception:
        return "GRIS"
