from fastapi import APIRouter, Request, Response
from twilio.twiml.messaging_response import MessagingResponse
from db.db import SessionLocal
from models.Debtor import Debtor 
from services.debtor_service import update_state
from services.openai_service import generate_openai_response_sync
import json

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/")
async def whatsapp_webhook(request: Request):
    form = await request.form()
    from_number = form.get("From")  # ej: 'whatsapp:+54911xxxxxxx'
    incoming_msg = form.get("Body")

    db = next(get_db())

    # Buscamos el deudor por teléfono
    debtor = db.query(Debtor).filter(Debtor.phone == from_number.replace("whatsapp:", "")).first()
    if debtor is None:
        # Si no está, crear nuevo deudor con historial vacío
        debtor = Debtor(phone=from_number.replace("whatsapp:", ""), conversation_history=json.dumps([]))
        db.add(debtor)
        db.commit()
        db.refresh(debtor)

    # Cargar historial de conversación (lista de dicts)
    if debtor.conversation_history:
        try:
            history = json.loads(debtor.conversation_history)
        except Exception:
            history = []
    else:
        history = []

    new_state = update_state(db,debtor.id,incoming_msg)
    debtor.state = new_state  # Asignás el nuevo estado directamente
    db.commit()

    # Prompt base del bot (puede venir de la campaña o configuración)
    prompt_base = "Sos un bot de cobranzas. Respondé de forma amable pero firme."


    # ACA PODRIA AGREGAR DEBTOR Y TODOS SUS DATOS
    
    # Armamos mensajes para OpenAI: prompt system + historial + nuevo mensaje user
    messages_for_openai = [{"role": "system", "content": prompt_base}] + history + [{"role": "user", "content": incoming_msg} ]

    # Llamamos OpenAI con lista de mensajes
    response_text = generate_openai_response_sync(messages_for_openai)

    # Actualizamos historial agregando el mensaje user y respuesta assistant
    history.append({"role": "user", "content": incoming_msg})
    history.append({"role": "assistant", "content": response_text})

    # Guardamos historial actualizado en DB (como JSON string)
    debtor.conversation_history = json.dumps(history)
    db.commit()

    # Respondemos por WhatsApp
    twilio_response = MessagingResponse()
    twilio_response.message(response_text)
    return Response(content=str(twilio_response), media_type="application/xml")
