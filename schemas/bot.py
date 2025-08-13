from pydantic import BaseModel, ConfigDict
from typing import Optional, Dict
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

    model_config = ConfigDict(from_attributes=True)