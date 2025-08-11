from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, cast, String, Numeric, asc, desc
from sqlalchemy.sql import func # Import func specifically for database functions
from dependencies.auth import get_current_user
from models.User import User
from models.Debtor import Debtor
from models.DebtorDataset import DebtorDataset
from db.db import SessionLocal
from pydantic import BaseModel
from typing import List, Optional

from schemas.debtor import DebtorCreate, DebtorRead

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()



@router.post("/", response_model=DebtorRead)
def create_debtor(debtor: DebtorCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    dataset = db.query(DebtorDataset).filter(DebtorDataset.id == debtor.debtor_dataset_id, DebtorDataset.user_id == current_user.id).first()
    if not dataset:
        raise HTTPException(status_code=400, detail="Dataset not found or not owned by user")

    db_debtor = Debtor(
    phone=debtor.phone,
    state=debtor.state,
    debtor_dataset_id=debtor.debtor_dataset_id,
    custom_data=debtor.custom_data,
    user_id=current_user.id,
    )
    db.add(db_debtor)
    db.commit()
    db.refresh(db_debtor)
    return db_debtor

@router.get("/", response_model=List[DebtorRead])
def list_debtors(
    dataset_id: int = Query(...),
    search: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    min_amount: Optional[float] = Query(None),
    max_amount: Optional[float] = Query(None),
    sort_by: Optional[str] = Query(None),
    sort_direction: Optional[str] = Query(None, regex="^(asc|desc)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    dataset = db.query(DebtorDataset).filter(DebtorDataset.id == dataset_id, DebtorDataset.user_id == current_user.id).first()
    if not dataset:
        raise HTTPException(status_code=400, detail="Dataset not found or not owned by user")

    query = db.query(Debtor).filter(
        Debtor.debtor_dataset_id == dataset_id,
        Debtor.user_id == current_user.id
    )

    # Apply filters
    if search:
        search_pattern = f"%{search}%"
        # Robustly search across standard fields and all custom_data fields
        search_conditions = [
            cast(Debtor.phone, String).ilike(search_pattern),
            cast(Debtor.state, String).ilike(search_pattern),
            # Search common custom fields explicitly and safely
            cast(Debtor.custom_data.op('->>')('name'), String).ilike(search_pattern),
            cast(Debtor.custom_data.op('->>')('dni'), String).ilike(search_pattern),
            cast(Debtor.custom_data.op('->>')('email'), String).ilike(search_pattern),
            # Generic search across all custom_data values. This is more robust as it operates on text values.
            # We filter by the 'value' part of the key-value pair.
            # Temporarily commented out to debug 500 Internal Server Error with search
            # cast(Debtor.custom_data, String).ilike(search_pattern),
        ]
        query = query.filter(or_(*search_conditions))

    if state:
        query = query.filter(Debtor.state == state)

    if min_amount is not None:
        # Ensure 'deuda' exists before casting for filtering and use a safer access method
        query = query.filter(
            Debtor.custom_data.has_key('deuda'), # Check if the key exists
            cast(Debtor.custom_data.op('->>')('deuda'), Numeric) >= min_amount
        )

    if max_amount is not None:
        # Ensure 'deuda' exists before casting for filtering and use a safer access method
        query = query.filter(
            Debtor.custom_data.has_key('deuda'), # Check if the key exists
            cast(Debtor.custom_data.op('->>')('deuda'), Numeric) <= max_amount
        )

    # Apply sorting
    if sort_by:
        sort_column = None
        if sort_by == 'phone':
            sort_column = Debtor.phone
        elif sort_by == 'state':
            sort_column = Debtor.state
        elif sort_by == 'deuda':
            # Need to cast to Numeric for proper sorting of amount, handling potential nulls from missing key
            # Use .op('->>') for safer key access which returns NULL if key is missing
            sort_column = cast(Debtor.custom_data.op('->>')('deuda'), Numeric)
        else:
            # Assume other sort_by fields are within custom_data
            # Use .op('->>') for safer key access which returns NULL if key is missing
            sort_column = Debtor.custom_data.op('->>')(sort_by)

        # No need for if sort_column: check, it's handled by not calling order_by if sort_column is None
        if sort_direction == 'desc':
            query = query.order_by(desc(sort_column))
        else: # Default to asc
            query = query.order_by(asc(sort_column))
    else:
        # Default sort order if no sort_by is provided (e.g., by ID or phone)
        query = query.order_by(Debtor.id) # Or Debtor.phone for a more user-friendly default

    debtors = query.all()
    return debtors

@router.delete("/{id}", status_code=204)
def delete_debtor(id: int, dataset_id: int = Query(...), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # First, verify the dataset belongs to the user
    dataset = db.query(DebtorDataset).filter(DebtorDataset.id == dataset_id, DebtorDataset.user_id == current_user.id).first()
    if not dataset:
        raise HTTPException(status_code=400, detail="Dataset not found or not owned by user")

    # Then, find the debtor within that dataset and owned by the user
    db_debtor = db.query(Debtor).filter(
        Debtor.id == id,
        Debtor.debtor_dataset_id == dataset_id,
        Debtor.user_id == current_user.id
    ).first()
    if not db_debtor:
        raise HTTPException(status_code=404, detail="Debtor not found in this dataset or not owned by user")
    db.delete(db_debtor)
    db.commit()
    return

@router.put("/{id}", response_model=DebtorRead)
def update_debtor(id: int, debtor: DebtorCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # First, verify the dataset belongs to the user
    dataset = db.query(DebtorDataset).filter(DebtorDataset.id == debtor.debtor_dataset_id, DebtorDataset.user_id == current_user.id).first()
    if not dataset:
        raise HTTPException(status_code=400, detail="Dataset not found or not owned by user")

    # Then, find the debtor within that dataset and owned by the user
    db_debtor = db.query(Debtor).filter(
        Debtor.id == id,
        Debtor.debtor_dataset_id == debtor.debtor_dataset_id,
        Debtor.user_id == current_user.id
    ).first()

    if not db_debtor:
        raise HTTPException(status_code=404, detail="Debtor not found in this dataset or not owned by user")

    for key, value in debtor.dict(exclude_unset=True).items():
        if key == "custom_data":
            db_debtor.custom_data.update(value)
        else:
            setattr(db_debtor, key, value)

    db.commit()
    db.refresh(db_debtor)
    return db_debtor
