from sqlalchemy import Column, Integer, String, DateTime, func
from db.db import Base
from sqlalchemy.orm import relationship

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    role = Column(String, default="user", nullable=False)


    campaigns = relationship("Campaign", back_populates="user")
    debtors = relationship("Debtor", back_populates="user")
    strategies = relationship("Strategy", back_populates="user")
    bots = relationship("Bot", back_populates="user")
    debtor_datasets = relationship("DebtorDataset", back_populates="user", cascade="all, delete-orphan")

