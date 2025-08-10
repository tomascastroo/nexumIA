# 📂 Ruta: schemas/conversation.py
# 🔗 Abrir archivo: file://./schemas/conversation.py

from pydantic import BaseModel, ConfigDict
from typing import List, Dict, Any, Optional

class Conversation(BaseModel):
    conversation_id: str
    history: List[Dict[str, str]]
    state: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class ConversationUpdate(BaseModel):
    conversation_id: str
    response: str
    history: List[Dict[str, str]]
    state: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)