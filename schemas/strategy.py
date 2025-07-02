from typing import Dict, Optional
from pydantic import BaseModel
from datetime import datetime

class StrategyBase(BaseModel):
    name: str
    initial_prompt: str = None
    rules_by_state: Optional[Dict] = None


class StrategyCreate(StrategyBase):
    pass

class StrategyRead(StrategyBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class StrategyUpdate(BaseModel):
    name: Optional[str] = None
    initial_prompt: str = None
    rules_by_state: Optional[Dict] = None
