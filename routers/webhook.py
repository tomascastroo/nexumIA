from fastapi import APIRouter, Request, Response
from twilio.twiml.messaging_response import MessagingResponse
from db.db import SessionLocal
from models.Debtor import Debtor 
from services.debtor_service import update_state
from services.openai_service import generate_openai_response_sync
import json
from services.conversation_service import handle_incoming_message as handle_conversation
from tasks.ia_tasks import process_incoming_message
from typing import List, Dict, Any, cast
from core.logger import log_business_event

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

    # Encolar el procesamiento para backpressure
    process_incoming_message.delay(cleaned_number, incoming_msg)
    log_business_event("webhook_enqueued", details={"phone": cleaned_number})
    
    # Responder rápido a Twilio para evitar timeouts
    twilio_response = MessagingResponse()
    twilio_response.message("Gracias, procesaremos tu mensaje.")
    return Response(content=str(twilio_response), media_type="application/xml")


