from .celery_app import celery_app
import structlog
from prometheus_client import Counter

logger = structlog.get_logger()
whatsapp_sent_counter = Counter('whatsapp_messages_sent', 'Total WhatsApp messages sent')

@celery_app.task
def send_whatsapp_message(payload):
    logger.info("Enviando mensaje WhatsApp", payload=payload)
    # Aquí iría la lógica real de envío
    whatsapp_sent_counter.inc()
    return {"status": "sent", "payload": payload} 