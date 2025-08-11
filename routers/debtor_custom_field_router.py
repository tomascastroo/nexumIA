from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session
from typing import List
from dependencies.auth import get_current_user
from models.User import User
from schemas.debtor_custom_field import DebtorCustomFieldCreate, DebtorCustomFieldRead, DebtorCustomFieldUpdate
from services import debtor_custom_field_service
from db.db import SessionLocal

router = APIRouter(prefix="/debtor-datasets/{dataset_id}/custom-fields", tags=["DebtorCustomFields"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=DebtorCustomFieldRead)
def create_custom_field(
    dataset_id: int,
    field: DebtorCustomFieldCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return debtor_custom_field_service.create_custom_field(db, dataset_id, field, user_id=current_user.id)

@router.get("/", response_model=List[DebtorCustomFieldRead])
def read_custom_fields(
    dataset_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return debtor_custom_field_service.get_custom_fields(db, dataset_id, user_id=current_user.id, skip=skip, limit=limit)

@router.get("/{field_id}", response_model=DebtorCustomFieldRead)
def read_custom_field(
    dataset_id: int,
    field_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_field = debtor_custom_field_service.get_custom_field(db, field_id, user_id=current_user.id)
    if not db_field:
        raise HTTPException(status_code=404, detail="Custom field not found")
    return db_field

@router.put("/{field_id}", response_model=DebtorCustomFieldRead)
def update_custom_field(
    dataset_id: int,
    field_id: int,
    field_update: DebtorCustomFieldUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_field = debtor_custom_field_service.update_custom_field(db, field_id, field_update, user_id=current_user.id)
    if not db_field:
        raise HTTPException(status_code=404, detail="Custom field not found")
    return db_field

@router.delete("/{field_id}", response_model=DebtorCustomFieldRead)
def delete_custom_field(
    dataset_id: int,
    field_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_field = debtor_custom_field_service.delete_custom_field(db, field_id, user_id=current_user.id)
    if not db_field:
        raise HTTPException(status_code=404, detail="Custom field not found")
    return db_field
