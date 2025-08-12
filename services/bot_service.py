"""
Este servicio espera que todas las funciones reciban la sesión de base de datos (db: Session) inyectada por el router vía Depends(get_db). No crear la sesión internamente.
"""
from sqlalchemy.orm import Session
from models.Bot import Bot
from schemas.campaign import CampaignCreate
from schemas.bot import BotCreate, BotUpdate


# NOTA: Este servicio devuelve objetos ORM. La conversión a Pydantic debe hacerse en el router usando .model_validate(obj, from_attributes=True)
def get_bot(db: Session,bot_id:int,user_id:int):
    return db.query(Bot).filter(Bot.id == bot_id, Bot.user_id == user_id).first()

def get_bots(db: Session,user_id:int, skip: int = 0, limit: int = 100):
    return db.query(Bot).filter(Bot.user_id == user_id).offset(skip).limit(limit).all()

def create_bot(db:Session,bot:BotCreate,user_id:int):
    db_bot = Bot(name=bot.name, config=bot.config, user_id=user_id)
    db.add(db_bot)
    db.commit()
    db.refresh(db_bot)
    return db_bot

def update_bot(db:Session,bot_id:int, bot:BotUpdate,user_id:int):
    db_bot = get_bot(db,bot_id,user_id=user_id)
    if not db_bot:
        return  None
    for var, value in vars(bot).items():
        setattr(db_bot,var,value) if value else None
    db.commit()
    db.refresh(db_bot)
    return db_bot

def delete_bot(db:Session,bot_id:int,user_id:int):
    db_bot = get_bot(db,bot_id,user_id=user_id)
    if not db_bot:
        return None
    db.delete(db_bot)
    db.commit()
    return db_bot
