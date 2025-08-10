from typing import List
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from dependencies.auth import get_current_user
from models.User import User
import schemas
from services import bot_service
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
    return BotRead.model_validate(db_bot, from_attributes=True)


@router.get("/", response_model=List[BotRead])
def get_bots(skip: int = 0, limit: int = 100, db: Session = Depends(get_db),current_user: User = Depends(get_current_user)):
    result = bot_service.get_bots(db,user_id=current_user.id, skip=skip, limit=limit)
    return [BotRead.model_validate(b, from_attributes=True) for b in result]

@router.delete("/{bot_id}",response_model=BotRead)
def delete_bot(bot_id:int,db:Session=Depends(get_db),current_user: User = Depends(get_current_user)):
    db_bot= bot_service.delete_bot(db,bot_id,user_id=current_user.id)
    if db_bot is None:
        raise HTTPException(status_code=404, detail="Bot not found")
    return db_bot
