from twilio.rest import Client

TWILIO_ACCOUNT_SID = "ACffc806caddc739c72dabd1419500fdb5"
TWILIO_AUTH_TOKEN = "27a4f5a28498cbf0f2a8c014362863a3"
TWILIO_WHATSAPP_NUMBER = "whatsapp:+14155238886"  # Número oficial Twilio WhatsApp

client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

def send_whatsapp_message(to: str, message: str) -> str:
    """
    Envía mensaje WhatsApp usando Twilio.
    `to` debe incluir 'whatsapp:' y código internacional, ej: 'whatsapp:+54911xxxxxxx'
    """
    msg = client.messages.create(
        body=message,
        from_=TWILIO_WHATSAPP_NUMBER,
        to=to
    )
    return msg.sid

