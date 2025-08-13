from fastapi import APIRouter, HTTPException
import sys
sys.path.append('.')
from db.db import SessionLocal
from services.whatsapp_service import send_whatsapp_message
from services.openai_service import generate_response_async, get_task_result


router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/send-whatsapp")
async def send_whatsapp():
    to = "whatsapp:+61415837604"

    # Encolar la generación de respuesta en Celery
    task_id = generate_response_async(
        [{"role": "user", "content": "sos un bot de cobranzas que deb convencer a que pague"}], 
        "gpt-4o-mini"
    )
    # Esperar el resultado (en producción esto podría ser asíncrono)
    message = get_task_result(task_id, timeout=30)
    if message is None:
        message = "Error generando respuesta"

    try:
        message_sid = send_whatsapp_message(to, message)
        return {"status": "success", "message_sid": message_sid}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



