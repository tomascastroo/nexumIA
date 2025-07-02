from datetime import datetime
from sqlalchemy import Column, ForeignKey, Integer, String, JSON, DateTime
from sqlalchemy.orm import relationship
from db.db import Base  

class Strategy(Base):
    __tablename__ = "strategies"

    id = Column(Integer, primary_key=True)
    name = Column(String, index=True)
    initial_prompt = Column(String, nullable=True)
    rules_by_state = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    campaigns = relationship("Campaign", back_populates="strategy")
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="strategies")