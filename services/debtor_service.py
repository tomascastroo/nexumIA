"""
Este servicio espera que todas las funciones reciban la sesión de base de datos (db: Session) inyectada por el router vía Depends(get_db). No crear la sesión internamente.
"""
from datetime import datetime
from fastapi import HTTPException
import json
from sqlalchemy.orm import Session
from models.Debtor import Debtor
from schemas.debtor import DebtorCreate, DebtorUpdate
from services.openai_service import classify_state_async, get_task_result

class DebtorNotFound(Exception):
    pass


def get_debtor(db: Session, debtor_id: int, user_id: int):
    return db.query(Debtor).filter(Debtor.id == debtor_id, Debtor.user_id == user_id).first()

def get_debtor_by_dni(db: Session, dni: str, user_id: int):
    return db.query(Debtor).filter(Debtor.dni == dni, Debtor.user_id == user_id).first()

def get_debtors(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    return db.query(Debtor).filter(Debtor.user_id == user_id).offset(skip).limit(limit).all()

def create_debtor(db: Session, debtor: DebtorCreate, user_id: int):
    existing = db.query(Debtor).filter_by(dni=debtor.dni, user_id=user_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Ya existe un deudor con ese DNI para este usuario")
    db_debtor = Debtor(**debtor.dict(), user_id=user_id)
    db.add(db_debtor)
    db.commit()
    db.refresh(db_debtor)
    return db_debtor

def update_debtor(db: Session, debtor_id: int, update_data: DebtorUpdate, user_id: int):
    db_debtor = get_debtor(db, debtor_id, user_id=user_id)
    if not db_debtor:
        return None
    for key, value in update_data.dict(exclude_unset=True).items():
        setattr(db_debtor, key, value)
    db.commit()
    db.refresh(db_debtor)
    return db_debtor

def delete_debtor(db: Session, debtor_id: int, user_id: int):
    db_debtor = get_debtor(db, debtor_id, user_id=user_id)
    if not db_debtor:
        return None
    db.delete(db_debtor)
    db.commit()
    return db_debtor

def update_state(db: Session, debtor_id: int, message: str, user_id: int = None):
    # Obtener el deudor filtrando por user_id si está dado
    query = db.query(Debtor).filter(Debtor.id == debtor_id)
    if user_id is not None:
        query = query.filter(Debtor.user_id == user_id)
    db_debtor = query.first()
    if not db_debtor:
        return "GRIS"
    
    # Cargar historial conversación
    conversation_history = []
    if db_debtor.conversation_history:
        try:
            conversation_history = json.loads(db_debtor.conversation_history)
        except json.JSONDecodeError:
            conversation_history = []

    current_state = db_debtor.state or "GRIS"
    
    # Obtener nuevo estado con IA usando Celery
    task_id = classify_state_async(message, conversation_history)
    new_state = get_task_result(task_id, timeout=30)
    if new_state is None:
        new_state = "GRIS"
    
    # Evitar bajar estado si hay contexto de pago
    if current_state in ["VERDE", "AMARILLO"]:
        message_lower = message.lower()
        payment_keywords = ['link', 'pago', 'pagar', 'deuda', 'cuenta', 'regularizar', 'sí', 'si', 'acepto', 'quiero']
        if new_state == "GRIS":
            if any(k in message_lower for k in payment_keywords):
                return current_state
            if message.strip().isdigit() and len(message.strip()) >= 7:
                return current_state
    
    if new_state != current_state:
        db_debtor.state = new_state
        db_debtor.updated_state = datetime.utcnow()
        db.commit()

    return new_state
