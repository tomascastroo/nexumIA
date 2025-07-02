from fastapi import APIRouter, Depends, Form, HTTPException, Request, Response
from pytest import Session
from twilio.twiml.messaging_response import MessagingResponse
from db.db import SessionLocal
from routers.bot import get_db
from services.whatsapp_service import send_whatsapp_message
from services.openai_service import generate_openai_response_sync
import asyncio


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

    loop = asyncio.get_event_loop()
    message = await loop.run_in_executor(
        None,
        lambda: generate_openai_response_sync("sos un bot de cobranzas que deb convencer a que pague", "gpt-4o-mini")
    )

    try:
        message_sid = send_whatsapp_message(to, message)
        return {"status": "success", "message_sid": message_sid}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



