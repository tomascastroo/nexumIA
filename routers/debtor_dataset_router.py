import io
import pandas as pd
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session
from typing import List
from dependencies.auth import get_current_user
from models.DebtorCustomField import DebtorCustomField
from models.DebtorDataset import DebtorDataset
from models.Debtor import Debtor
from models.User import User
from schemas.debtor_dataset import DebtorDatasetCreate, DebtorDatasetRead, DebtorDatasetUpdate
from services import debtor_dataset_service
from db.db import SessionLocal
from datetime import datetime


router = APIRouter(prefix="/debtor-datasets", tags=["DebtorDatasets"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()





@router.post("/", response_model=DebtorDatasetRead)
def create_dataset(
    dataset: DebtorDatasetCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return debtor_dataset_service.create_debtor_dataset(db, dataset, user_id=current_user.id)

@router.get("/", response_model=List[DebtorDatasetRead])
def read_datasets(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return debtor_dataset_service.get_debtor_datasets(db, user_id=current_user.id, skip=skip, limit=limit)

@router.get("/{dataset_id}", response_model=DebtorDatasetRead)
def read_dataset(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_dataset = debtor_dataset_service.get_debtor_dataset(db, dataset_id, user_id=current_user.id)
    if not db_dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return db_dataset

@router.put("/{dataset_id}", response_model=DebtorDatasetRead)
def update_dataset(
    dataset_id: int,
    dataset_update: DebtorDatasetUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_dataset = debtor_dataset_service.update_debtor_dataset(db, dataset_id, dataset_update, user_id=current_user.id)
    if not db_dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return db_dataset

@router.delete("/{dataset_id}", response_model=DebtorDatasetRead)
def delete_dataset(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_dataset = debtor_dataset_service.delete_debtor_dataset(db, dataset_id, user_id=current_user.id)
    if not db_dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return db_dataset




#  CARGAR ARCHIVOS
def convert_values_to_serializable(data):
    for k, v in data.items():
        if pd.isna(v):
            data[k] = None
        elif isinstance(v, (pd.Timestamp, datetime)):
            data[k] = v.isoformat()
        elif isinstance(v, dict):
            data[k] = convert_values_to_serializable(v)
    return data


@router.post("/upload-dataset/")
async def upload_dataset(
    file: UploadFile = File(...),
    dataset_name: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 1. Leer archivo
    if file.filename.endswith(".xlsx"):
        content = await file.read()  # leer bytes
        bytes_io = io.BytesIO(content)  # buffer con seek
        df = pd.read_excel(bytes_io)
    elif file.filename.endswith(".csv") or file.filename.endswith(".txt"):
        content = await file.read()
        df = pd.read_csv(io.BytesIO(content), sep=None, engine="python")
    else:
        raise HTTPException(status_code=400, detail="Formato de archivo no soportado")

    # 2. Validar campos necesarios
    if "phone" not in df.columns:
        raise HTTPException(status_code=400, detail="El archivo debe contener al menos la columna 'phone'")

    # 3. Crear dataset
    dataset = DebtorDataset(name=dataset_name, user_id=current_user.id)
    db.add(dataset)
    db.commit()
    db.refresh(dataset)

    # 4. Crear campos personalizados
    standard_fields = {"phone", "dni", "email", "state"}
    for col in df.columns:
        if col in standard_fields:
            continue
        sample = df[col].dropna().iloc[0] if not df[col].dropna().empty else ""
        if isinstance(sample, (int, float)):
            field_type = "float"
        elif isinstance(sample, datetime):
            field_type = "date"
        else:
            field_type = "string"

        db_field = DebtorCustomField(
            name=col,
            field_type=field_type,
            debtor_dataset_id=dataset.id
        )
        db.add(db_field)

    db.commit()

    # 5. Crear deudores
    for _, row in df.iterrows():
        phone = str(row.get("phone"))
        dni = str(row.get("dni")) if "dni" in row else None
        email = row.get("email") if "email" in row else None
        state = row.get("state") if "state" in row else "GRIS"

        # custom_data
        custom_data = {}
        for col in df.columns:
            if col in standard_fields:
                continue
            value = row[col]
            if pd.isna(value):
                continue
            custom_data[col] = value

        # Convertir campos no serializables a string ISO
        custom_data = convert_values_to_serializable(custom_data)

        debtor = Debtor(
            phone=phone,
            user_id=current_user.id,
            debtor_dataset_id=dataset.id,
            state=state,
            conversation_history=[],
            custom_data=custom_data
        )
        if dni:
            debtor.dni = dni
        if email:
            debtor.email = email

        db.add(debtor)

    db.commit()

    return {
        "message": "Dataset creado con éxito",
        "dataset_id": dataset.id,
        "deudores_cargados": len(df)
    }