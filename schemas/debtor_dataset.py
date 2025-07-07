from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class DebtorDatasetBase(BaseModel):
    name: str

class DebtorDatasetCreate(DebtorDatasetBase):
    pass

class DebtorDatasetUpdate(BaseModel):
    name: Optional[str]

class DebtorDatasetRead(DebtorDatasetBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
