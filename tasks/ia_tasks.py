from .celery_app import celery_app
import structlog
from prometheus_client import Counter
from db.db import SessionLocal
from services.conversation_service import handle_incoming_message
from services.whatsapp_service import send_whatsapp_message

logger = structlog.get_logger()
ia_task_counter = Counter('ia_tasks_executed', 'Total IA tasks executed')

@celery_app.task
def save_conversation(conversation):
    logger.info("Guardando conversación IA", conversation=conversation)
    ia_task_counter.inc()
    # Lógica de guardado
    return {"status": "saved"}

@celery_app.task
def analyze_debtors(debtors):
    logger.info("Análisis masivo de deudores", count=len(debtors))
    ia_task_counter.inc()
    # Lógica de análisis
    return {"status": "analyzed", "count": len(debtors)} 


@celery_app.task
def process_incoming_message(phone: str, body: str):
    """Backpressure task: procesa mensaje entrante con IA y responde por WhatsApp en background."""
    logger.info("Procesando mensaje entrante en background", phone=phone)
    ia_task_counter.inc()
    db = SessionLocal()
    try:
        response_text = handle_incoming_message(phone, body, db)
        # handle_incoming_message es async; si devuelve coroutine, resolver
        if hasattr(response_text, "__await__"):
            response_text = response_text.send(None)  # no event loop in worker, best-effort
        if not response_text:
            response_text = "Gracias, recibimos tu mensaje. Te responderemos pronto."
        send_whatsapp_message(f"whatsapp:{phone}", response_text)
        return {"status": "sent", "phone": phone}
    except Exception as e:
        logger.error("Error en process_incoming_message", error=str(e))
        return {"status": "error", "error": str(e)}
    finally:
        db.close()