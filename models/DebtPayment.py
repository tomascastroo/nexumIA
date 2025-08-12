from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from db.db import Base

class DebtPayment(Base):
    __tablename__ = "debt_payments"

    id = Column(Integer, primary_key=True, index=True)
    debtor_id = Column(Integer, ForeignKey("debtors.id"), nullable=False, index=True)
    amount_requested = Column(Float, nullable=False)
    amount_paid = Column(Float, nullable=True)
    discount_applied = Column(Float, nullable=True)
    status = Column(String, nullable=False, default="pending")  # pending, paid, failed, expired, cancelled
    payment_link = Column(String, nullable=True)
    method = Column(String, nullable=True)  # e.g., "mercadopago", "stripe"
    external_reference = Column(String, nullable=True)  # ID del proveedor externo
    paid_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=True)
    rule_id = Column(String, nullable=True)  # ID o nombre de la regla que originó el pago

    debtor = relationship("Debtor", back_populates="debt_payments")
    campaign = relationship("Campaign", back_populates="debt_payments") 