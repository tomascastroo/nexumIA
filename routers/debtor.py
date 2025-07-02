from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from db.db import SessionLocal
from models.User import User
from schemas.debtor import DebtorCreate, DebtorRead, DebtorUpdate
from services import debtor_service
from typing import List
from dependencies.auth import get_current_user

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/", response_model=DebtorRead)
def create_debtor(debtor: DebtorCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return debtor_service.create_debtor(db, debtor,user_id=current_user.id)

@router.get("/", response_model=List[DebtorRead])
def read_debtors(skip: int = 0, limit: int = 100, db: Session = Depends(get_db),current_user: User = Depends(get_current_user)):
    return debtor_service.get_debtors(db,user_id = current_user.id, skip=skip, limit=limit)

@router.get("/{debtor_id}", response_model=DebtorRead)
def read_debtor(debtor_id: int, db: Session = Depends(get_db),current_user: User = Depends(get_current_user)):
    db_debtor = debtor_service.get_debtor(db, debtor_id,user_id = current_user.id)
    if db_debtor is None:
        raise HTTPException(status_code=404, detail="Debtor not found")
    return db_debtor

@router.put("/{debtor_id}", response_model=DebtorRead)
def update_debtor(debtor_id: int, debtor: DebtorUpdate, db: Session = Depends(get_db),current_user: User = Depends(get_current_user)):
    db_debtor = debtor_service.update_debtor(db, debtor_id, debtor,user_id = current_user.id)
    if db_debtor is None:
        raise HTTPException(status_code=404, detail="Debtor not found")
    return db_debtor

@router.delete("/{debtor_id}", response_model=DebtorRead)
def delete_debtor(debtor_id: int, db: Session = Depends(get_db),current_user: User = Depends(get_current_user)):
    db_debtor = debtor_service.delete_debtor(db, debtor_id,user_id = current_user.id)
    if db_debtor is None:
        raise HTTPException(status_code=404, detail="Debtor not found")
    return db_debtor
