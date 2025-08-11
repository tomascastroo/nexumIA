from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from db.db import Base

# Importá explícitamente las clases relacionadas para que existan en el momento
from models.DebtorCustomField import DebtorCustomField
from models.Debtor import Debtor
from models.User import User
from models.Campaign import Campaign

class DebtorDataset(Base):
    __tablename__ = "debtor_datasets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="debtor_datasets")
    debtors = relationship("Debtor", back_populates="debtor_dataset", cascade="all, delete-orphan")
    custom_fields = relationship("DebtorCustomField", back_populates="debtor_dataset", cascade="all, delete-orphan")
    campaigns = relationship("Campaign", back_populates="debtor_dataset")
