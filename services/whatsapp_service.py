import os
from twilio.rest import Client

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_WHATSAPP_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER", "whatsapp:+14155238886")

# Bandera para deshabilitar servicios externos en tests/CI
DISABLE_EXTERNAL_SERVICES = os.getenv("DISABLE_EXTERNAL_SERVICES", "false").lower() == "true"

_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN) if (TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN) else None

def send_whatsapp_message(to: str, message: str) -> str:
    # En tests/CI o sin credenciales válidas, no llamar a Twilio
    if DISABLE_EXTERNAL_SERVICES or _client is None:
        return "mocked-twilio-sid"
    msg = _client.messages.create(
        body=message,
        from_=TWILIO_WHATSAPP_NUMBER,
        to=to
    )
    return msg.sid

