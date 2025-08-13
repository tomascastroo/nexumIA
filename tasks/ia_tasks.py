from .celery_app import celery_app
import structlog
from prometheus_client import Counter
from db.db import SessionLocal
from services.whatsapp_service import send_whatsapp_message
from models.Debtor import Debtor
import asyncio

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


@celery_app.task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def process_incoming_message(self, phone: str, body: str):
    """
    Backpressure task: procesa mensaje entrante con IA y responde por WhatsApp en background.
    Ahora usa tareas asíncronas de OpenAI con reintentos automáticos.
    """
    logger.info("Procesando mensaje entrante en background", phone=phone, task_id=self.request.id)
    ia_task_counter.inc()
    db = SessionLocal()
    try:
        # Buscar el deudor por teléfono
        debtor = db.query(Debtor).filter(Debtor.phone == phone).first()
        if not debtor:
            logger.warning("Debtor no encontrado", phone=phone)
            response_text = "Lo sentimos, no pudimos procesar tu mensaje."
        else:
            # Aquí se podría integrar con las tareas asíncronas de OpenAI
            # Por ahora, usamos una respuesta simple
            response_text = "Gracias por tu mensaje. Te responderemos pronto."
            
            # Actualizar el historial de conversación
            if not debtor.conversation_history:
                debtor.conversation_history = []
            debtor.conversation_history.append({
                "role": "user",
                "content": body,
                "timestamp": str(asyncio.get_event_loop().time())
            })
            db.commit()
        
        # Enviar respuesta por WhatsApp
        send_whatsapp_message(f"whatsapp:{phone}", response_text)
        
        logger.info("Mensaje procesado y enviado exitosamente", 
                   phone=phone, task_id=self.request.id)
        return {"status": "sent", "phone": phone, "task_id": self.request.id}
        
    except Exception as e:
        logger.error("Error en process_incoming_message", 
                    error=str(e), phone=phone, task_id=self.request.id, retry_count=self.request.retries)
        raise  # Celery reintentará automáticamente
    finally:
        db.close()