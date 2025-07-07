from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from schemas.bot import BotRead
from schemas.debtor import DebtorRead
from schemas.debtor_dataset import DebtorDatasetRead
from schemas.strategy import StrategyRead

class CampaignBase(BaseModel):
    name: str
    bot_id: int
    strategy_id: int
    status: Optional[str] = "inactive"
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

class CampaignCreate(BaseModel):
    name: str
    bot_id: Optional[int] = None
    strategy_id: int
    debtor_dataset_id: int
    status: Optional[str] = "inactive"
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

class CampaignUpdate(BaseModel):
    name: Optional[str]
    bot_id: Optional[int]
    strategy_id: Optional[int]
    status: Optional[str]
    start_date: Optional[datetime]
    end_date: Optional[datetime]

    class Config:
        orm_mode = True

class CampaignRead(BaseModel):
    id: int
    name: str
    bot_id: Optional[int] = None
    strategy_id: Optional[int] = None
    status: Optional[str]
    start_date: Optional[datetime]
    end_date: Optional[datetime]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    debtor_dataset_id: Optional[int] = None
    strategy: Optional[StrategyRead] = None
    bot: Optional[BotRead] = None  # opcional si querés mostrarlo
    debtor_dataset: Optional[DebtorDatasetRead] = None


    class Config:
        orm_mode = True
        from_attributes = True


class CampaignReadMinimal(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True
