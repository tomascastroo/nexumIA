from pydantic import BaseModel, EmailStr
from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from schemas.campaign import CampaignReadMinimal  # Solo para type hints

class DebtorBase(BaseModel):
    name: str
    dni: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None

class DebtorCreate(BaseModel):
    phone: Optional[str]
    state: Optional[str] = "GRIS"
    debtor_dataset_id: int
    custom_data: dict = {}
    
class DebtorUpdate(DebtorBase):
    pass

class DebtorIDs(BaseModel):
    debtor_ids: List[int]



class DebtorRead(BaseModel):
    id: int
    phone: Optional[str]
    state: Optional[str]
    debtor_dataset_id: int
    custom_data: dict

    class Config:
        orm_mode = True