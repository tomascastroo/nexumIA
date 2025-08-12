import io
import pandas as pd
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status, Depends
from fastapi.responses import JSONResponse
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
    result = debtor_dataset_service.get_debtor_datasets(db, user_id=current_user.id, skip=skip, limit=limit)
    return [DebtorDatasetRead.model_validate(d, from_attributes=True) for d in result]

@router.get("/{dataset_id}", response_model=DebtorDatasetRead)
def read_dataset(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_dataset = debtor_dataset_service.get_debtor_dataset(db, dataset_id, user_id=current_user.id)
    if not db_dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return DebtorDatasetRead.model_validate(db_dataset, from_attributes=True)

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

@router.post("/upload-dataset/", status_code=200)
async def upload_dataset(
    file: UploadFile = File(...),
    dataset_name: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not file:
        raise HTTPException(status_code=400, detail="No se recibió ningún archivo.")

    allowed_types = [
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.ms-excel",
        "text/csv",
        "application/csv"
    ]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Tipo de archivo no soportado.")

    try:
        content = await file.read()
        if not content:
            raise HTTPException(status_code=400, detail="Archivo vacío.")
        if file.content_type.startswith("application/vnd.openxmlformats-officedocument") or file.filename.endswith(".xlsx"):
            df = pd.read_excel(io.BytesIO(content))
        else:
            df = pd.read_csv(io.BytesIO(content))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error leyendo el archivo: {str(e)}")

    if "phone" not in df.columns:
        raise HTTPException(status_code=400, detail="Debe contener columna 'phone'.")

    # Crear dataset
    new_dataset = DebtorDataset(
        name=dataset_name,
        user_id=current_user.id,
        created_at=datetime.utcnow()
    )
    db.add(new_dataset)
    db.commit()
    db.refresh(new_dataset)

    # Guardar custom fields
    for k in df.columns:
        if k not in ['phone', 'state']:
            # Detectar tipo de campo (opcional: puedes mejorar esto)
            value = df[k].dropna().iloc[0] if not df[k].dropna().empty else ""
            if isinstance(value, (pd.Timestamp, datetime)):
                field_type = "date"
            elif isinstance(value, (int, float)):
                field_type = "number"
            else:
                field_type = "string"
            custom_field = DebtorCustomField(
                name=k,
                field_type=field_type,
                debtor_dataset_id=new_dataset.id,
                created_at=datetime.utcnow()
            )
            db.add(custom_field)
    db.commit()

    # Guardar deudores
    for _, row in df.iterrows():
        custom_data = {}
        for k in df.columns:
            if k not in ['phone', 'state']:
                value = row[k]
                # Si es Timestamp de pandas, convertir a string ISO
                if hasattr(value, 'isoformat'):
                    value = value.isoformat()
                # Si es numpy.int64, convertir a int
                elif str(type(value)).startswith("<class 'numpy."):
                    value = value.item()
                custom_data[k] = value
        new_debtor = Debtor(
            debtor_dataset_id=new_dataset.id,
            phone=row.get('phone'),
            state=row.get('state', 'GRIS'),
            custom_data=custom_data,
            user_id=current_user.id  # si corresponde
        )
        db.add(new_debtor)
    db.commit()

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"message": f"Archivo '{file.filename}' subido correctamente para dataset '{dataset_name}'. Filas detectadas: {len(df)}"}
    )
