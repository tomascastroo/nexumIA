from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, JSON, func, TIMESTAMP
from sqlalchemy.orm import relationship
from db.db import Base

class Debtor(Base):
    __tablename__ = "debtors"

    id = Column(Integer, primary_key=True, index=True)
    debtor_dataset_id = Column(Integer, ForeignKey("debtor_datasets.id"), nullable=False)
    phone = Column(String, nullable=False, index=True)  # obligatorio y con índice
    state = Column(String, default="GRIS", index=True)  # estado inicial por defecto "GRIS"
    conversation_history = Column(JSON, default=list)  # historial de mensajes como lista JSON
    custom_data = Column(JSON, default=dict)  # campos personalizados dinámicos en JSON

    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)

    ultimo_contacto = Column(DateTime, nullable=True)
    proximo_contacto = Column(DateTime, nullable=True)

    user_id = Column(Integer, ForeignKey("users.id"))

    user = relationship("User", back_populates="debtors")
    debtor_dataset = relationship("DebtorDataset", back_populates="debtors")
    debt_payments = relationship("DebtPayment", back_populates="debtor", cascade="all, delete-orphan")
