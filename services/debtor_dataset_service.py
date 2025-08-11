from sqlalchemy.orm import Session
from fastapi import HTTPException
from models.DebtorDataset import DebtorDataset
from schemas.debtor_dataset import DebtorDatasetCreate, DebtorDatasetUpdate

def get_debtor_dataset(db: Session, dataset_id: int, user_id: int):
    return db.query(DebtorDataset).filter(DebtorDataset.id == dataset_id, DebtorDataset.user_id == user_id).first()

def get_debtor_datasets(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    return db.query(DebtorDataset).filter(DebtorDataset.user_id == user_id).offset(skip).limit(limit).all()

def create_debtor_dataset(db: Session, dataset: DebtorDatasetCreate, user_id: int):
    db_dataset = DebtorDataset(name=dataset.name, user_id=user_id)
    db.add(db_dataset)
    db.commit()
    db.refresh(db_dataset)
    return db_dataset

def update_debtor_dataset(db: Session, dataset_id: int, dataset_update: DebtorDatasetUpdate, user_id: int):
    db_dataset = get_debtor_dataset(db, dataset_id, user_id)
    if not db_dataset:
        return None
    for var, value in dataset_update.dict(exclude_unset=True).items():
        setattr(db_dataset, var, value)
    db.commit()
    db.refresh(db_dataset)
    return db_dataset

def delete_debtor_dataset(db: Session, dataset_id: int, user_id: int):
    db_dataset = get_debtor_dataset(db, dataset_id, user_id)
    if not db_dataset:
        return None
    db.delete(db_dataset)
    db.commit()
    return db_dataset
