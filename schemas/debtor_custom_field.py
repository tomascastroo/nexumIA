from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class DebtorCustomFieldBase(BaseModel):
    name: str
    field_type: str

class DebtorCustomFieldCreate(DebtorCustomFieldBase):
    pass

class DebtorCustomFieldUpdate(BaseModel):
    name: Optional[str]
    field_type: Optional[str]

class DebtorCustomFieldRead(DebtorCustomFieldBase):
    id: int
    debtor_dataset_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
