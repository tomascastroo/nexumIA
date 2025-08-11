from fastapi import APIRouter, Request, Response
from twilio.twiml.messaging_response import MessagingResponse
from db.db import SessionLocal
from models.Debtor import Debtor 
from services.debtor_service import update_state
from services.openai_service import generate_openai_response_sync
import json
from services.conversation_service import handle_incoming_message as handle_conversation
from typing import List, Dict, Any, cast

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def normalize_phone(raw_phone: str) -> str:
    # Ensure raw_phone is a string before replacement
    return raw_phone.replace("whatsapp:", "").replace("+", "").strip()


@router.post("/")
async def whatsapp_webhook(request: Request):
    form = await request.form()
    raw_number_form = form.get("From")  # ej: 'whatsapp:+54911xxxxxxx'
    incoming_msg_body = form.get("Body")

    # Ensure inputs are strings, provide empty string if None
    raw_number = str(raw_number_form) if raw_number_form is not None else ""
    incoming_msg = str(incoming_msg_body) if incoming_msg_body is not None else ""

    db = next(get_db())

    cleaned_number = normalize_phone(raw_number)
    debtor = db.query(Debtor).filter(Debtor.phone == cleaned_number).first()

    print(debtor) # Keep this debug print if useful

    if debtor is None:
        # If debtor not found, create a new one (minimal creation)
        debtor = Debtor(phone=cleaned_number, conversation_history=[]) # Use empty list for JSON default
        db.add(debtor)
        db.commit()
        db.refresh(debtor)

    # Centralize conversation handling to services/conversation_service.py
    await handle_conversation(cleaned_number, incoming_msg, db)
    
    # The response is now handled within handle_conversation, but Twilio expects an XML response.
    # We need to retrieve the last assistant message from the debtor's updated history
    # For this, we refresh the debtor object to get the latest state from the DB.
    db.refresh(debtor) # Refresh debtor to get updated conversation_history

    # Ensure conversation_history is treated as a list, as it's a JSON column
    updated_history: List[Dict[str, Any]] = cast(List[Dict[str, Any]], debtor.conversation_history) if debtor.conversation_history is not None else []
    response_text = "Lo siento, no pude generar una respuesta en este momento." # Default fallback

    if updated_history and isinstance(updated_history, list):
        last_message = updated_history[-1]
        if last_message and 'role' in last_message and last_message['role'] == 'assistant' and 'content' in last_message:
            response_text = last_message['content']

    # Respondemos por WhatsApp
    twilio_response = MessagingResponse()
    twilio_response.message(response_text)
    return Response(content=str(twilio_response), media_type="application/xml")


