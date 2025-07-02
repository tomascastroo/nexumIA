from sqlalchemy import Column, Date, Float, Integer, String, ForeignKey, JSON, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from db.db import Base


class Debtor(Base):
    __tablename__ = "debtors"

    id = Column(Integer, primary_key=True, index=True)
    dni = Column(String, index=True)      
    name = Column(String)
    email = Column(String, nullable=True)
    amount_due = Column(Float)
    due_date = Column(Date)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"))
    phone = Column(String)
    conversation_history = Column(JSON, default=[])
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    state = Column(String, default="NO_DEFINIDO")  # Valores como: VERDE, AMARILLO, ROJO
    updated_state = Column(DateTime, default=datetime.utcnow)

    campaign = relationship("Campaign", back_populates="debtors") 
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="debtors")