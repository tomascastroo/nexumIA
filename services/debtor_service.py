from datetime import datetime
from fastapi import HTTPException
from sqlalchemy.orm import Session
from models.Debtor import Debtor
from schemas.debtor import DebtorCreate, DebtorUpdate
from services.openai_service import classify_state

def get_debtor(db: Session, debtor_id: int,  user_id: int):
    return db.query(Debtor).filter(Debtor.id == debtor_id, Debtor.user_id == user_id).first()

def get_debtor_by_dni(db: Session, dni: str,user_id: int):
    return db.query(Debtor).filter(Debtor.dni == dni,  Debtor.user_id == user_id).first()

def get_debtors(db: Session,user_id: int, skip: int = 0, limit: int = 100):
    return db.query(Debtor).filter(Debtor.user_id == user_id).offset(skip).limit(limit).all()

def create_debtor(db: Session, debtor: DebtorCreate, user_id:int):

    existing = db.query(Debtor).filter_by(dni=debtor.dni, user_id=user_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Ya existe un deudor con ese DNI para este usuario")
    db_debtor = Debtor(**debtor.dict(), user_id=user_id)
    db.add(db_debtor)
    db.commit()
    db.refresh(db_debtor)
    return db_debtor

def update_debtor(db: Session, debtor_id: int, update_data: DebtorUpdate,user_id:int):
    db_debtor = get_debtor(db, debtor_id,user_id=user_id)
    if not db_debtor:
        return None
    for key, value in update_data.dict(exclude_unset=True).items():
        setattr(db_debtor, key, value)
    db.commit()
    db.refresh(db_debtor)
    return db_debtor

def delete_debtor(db: Session, debtor_id: int,user_id:int):
    db_debtor = get_debtor(db, debtor_id,user_id=user_id)
    if not db_debtor:
        return None
    db.delete(db_debtor)
    db.commit()
    return db_debtor


def update_state(db, debtor_id, message):
    new_state = classify_state(message)
    db_debtor = db.query(Debtor).get(debtor_id)
    db_debtor.state = new_state                # ✅ corregido
    db_debtor.updated_state = datetime.utcnow()
    db.commit()
    return new_state                           # ✅ si querés devolverlo
