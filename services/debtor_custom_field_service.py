from sqlalchemy.orm import Session
from fastapi import HTTPException
from models.DebtorDataset import DebtorDataset
from models.DebtorCustomField import DebtorCustomField
from schemas.debtor_custom_field import DebtorCustomFieldCreate, DebtorCustomFieldUpdate

def get_custom_field(db: Session, field_id: int, user_id: int):
    # Necesitamos join para validar user_id a través del dataset
    return db.query(DebtorCustomField).join("debtor_dataset").filter(
        DebtorCustomField.id == field_id,
        DebtorCustomField.debtor_dataset.has(user_id=user_id)
    ).first()

def get_custom_fields(db: Session, debtor_dataset_id: int, user_id: int, skip: int = 0, limit: int = 100):
    return db.query(DebtorCustomField).filter(
        DebtorCustomField.debtor_dataset_id == debtor_dataset_id,
        DebtorCustomField.debtor_dataset.has(user_id=user_id)
    ).offset(skip).limit(limit).all()


def create_custom_field(db: Session, debtor_dataset_id: int, field: DebtorCustomFieldCreate, user_id: int):
    # validar que dataset exista y pertenezca a usuario
    dataset = db.query(DebtorDataset).filter_by(id=debtor_dataset_id, user_id=user_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found or access denied")

    db_field = DebtorCustomField(
        debtor_dataset_id=debtor_dataset_id,
        name=field.name,         # <-- debe ser 'name' y no 'field_name'
        field_type=field.field_type
    )
    db.add(db_field)
    db.commit()
    db.refresh(db_field)
    return db_field


def update_custom_field(db: Session, field_id: int, field_update: DebtorCustomFieldUpdate, user_id: int):
    db_field = get_custom_field(db, field_id, user_id)
    if not db_field:
        return None
    for var, value in field_update.dict(exclude_unset=True).items():
        setattr(db_field, var, value)
    db.commit()
    db.refresh(db_field)
    return db_field

def delete_custom_field(db: Session, field_id: int, user_id: int):
    db_field = get_custom_field(db, field_id, user_id)
    if not db_field:
        return None
    db.delete(db_field)
    db.commit()
    return db_field
