from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime


class BotBase(BaseModel):
    name: str
    config: Optional[Dict] = None

class BotCreate(BotBase):
    pass

class BotUpdate(BaseModel):
    name: Optional[str] = None
    config: Optional[Dict] = None

class BotRead(BotBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True