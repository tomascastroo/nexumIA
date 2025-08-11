from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from db.db import Base

class Debtor(Base):
    __tablename__ = "debtors"

    id = Column(Integer, primary_key=True, index=True)
    debtor_dataset_id = Column(Integer, ForeignKey("debtor_datasets.id"), nullable=False)
    phone = Column(String, nullable=False, index=True)  # obligatorio y con índice
    state = Column(String, default="GRIS", index=True)  # estado inicial por defecto "GRIS"
    conversation_history = Column(JSON, default=list)  # historial de mensajes como lista JSON
    custom_data = Column(JSON, default=dict)  # campos personalizados dinámicos en JSON

    user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="debtors")
    debtor_dataset = relationship("DebtorDataset", back_populates="debtors")
