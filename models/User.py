from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from db.db import Base  


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    campaigns = relationship("Campaign", back_populates="user")
    debtors = relationship("Debtor", back_populates="user")
    strategies = relationship("Strategy", back_populates="user")
    bots = relationship("Bot", back_populates="user")
    debtor_datasets = relationship("DebtorDataset", back_populates="user", cascade="all, delete-orphan")

