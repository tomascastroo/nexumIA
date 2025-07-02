from pydantic import BaseModel, EmailStr
from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from schemas.campaign import CampaignReadMinimal  # Solo para type hints

class DebtorBase(BaseModel):
    name: str
    dni: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None

class DebtorCreate(DebtorBase):
    pass

class DebtorUpdate(DebtorBase):
    pass

class DebtorIDs(BaseModel):
    debtor_ids: List[int]



class DebtorRead(DebtorBase):
    id: int
    amount: Optional[float] = None
    status: Optional[str] = None
    # campaigns: List["CampaignReadMinimal"]

    class Config:
        from_attributes = True
