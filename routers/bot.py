from typing import List
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from dependencies.auth import get_current_user
from models.User import User
import schemas
from services import bot_interaction_service, bot_service
from db.db import SessionLocal
from schemas.bot import BotCreate, BotUpdate, BotRead


router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/",response_model=BotCreate)
def create_bot(bot: BotCreate,db: Session = Depends(get_db),current_user: User = Depends(get_current_user)):
    return bot_service.create_bot(db, bot, user_id=current_user.id)


@router.post("/{bot_id}",response_model=BotUpdate)
def update_bot(bot_id:int,bot:BotUpdate,db:Session=Depends(get_db),current_user: User = Depends(get_current_user)):
    db_bot = bot_service.update_bot(db,bot_id,bot,user_id=current_user.id)
    if db_bot is None:
        raise HTTPException(status_code=404, detail="Bot not found")
    return db_bot

@router.get("/{bot_id}",response_model=BotRead)
def get_bot(bot_id:int,db:Session=Depends(get_db),current_user: User = Depends(get_current_user)):
    db_bot= bot_service.get_bot(db,bot_id,user_id=current_user.id)
    if db_bot is None:
        raise HTTPException(status_code=404, detail="Bot not found")
    return db_bot


@router.get("/", response_model=List[BotRead])
def get_bots(skip: int = 0, limit: int = 100, db: Session = Depends(get_db),current_user: User = Depends(get_current_user)):
    return bot_service.get_bots(db,user_id=current_user.id, skip=skip, limit=limit)

@router.delete("/{bot_id}",response_model=BotRead)
def delete_bot(bot_id:int,db:Session=Depends(get_db),current_user: User = Depends(get_current_user)):
    db_bot= bot_service.delete_bot(db,bot_id,user_id=current_user.id)
    if db_bot is None:
        raise HTTPException(status_code=404, detail="Bot not found")
    return db_bot


# @router.post("/webhook/whatsapp")
# async def whatsapp_webhook(request: Request, background_tasks: BackgroundTasks):
#     data = await request.json()

#     # Extraer mensaje entrante según el formato API WhatsApp
#     try:
#         entry = data["entry"][0]
#         changes = entry["changes"][0]
#         value = changes["value"]
#         messages = value.get("messages", [])
#         if not messages:
#             return {"status": "no messages"}

#         msg = messages[0]
#         phone = msg["from"]  # número usuario que manda mensaje
#         text = msg["text"]["body"]

#         # Aquí tenés que saber a qué bot pertenece ese número (ejemplo estático)
#         bot_id = 1

#         # Ejecutar en background la respuesta para no bloquear webhook
#         background_tasks.add_task(bot_interaction_service.handle_incoming_message, bot_id, phone, text)

#         return {"status": "message received"}

#     except Exception as e:
#         return {"error": str(e)}
