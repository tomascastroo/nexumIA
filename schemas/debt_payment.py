from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class PaymentRequest(BaseModel):
    debtor_id: int
    amount_requested: float
    discount_applied: Optional[float] = None
    campaign_id: Optional[int] = None
    rule_id: Optional[str] = None
    method: Optional[str] = "mock"  # "mercadopago", "stripe", "mock"

class DebtPaymentIn(BaseModel):
    debtor_id: int
    amount_requested: float
    discount_applied: Optional[float] = None
    campaign_id: Optional[int] = None
    rule_id: Optional[str] = None
    method: Optional[str] = "mock"

class DebtPaymentOut(BaseModel):
    id: int
    debtor_id: int
    amount_requested: float
    amount_paid: Optional[float]
    discount_applied: Optional[float]
    status: str
    payment_link: Optional[str]
    method: Optional[str]
    external_reference: Optional[str]
    paid_at: Optional[datetime]
    created_at: datetime
    expires_at: Optional[datetime]
    campaign_id: Optional[int]
    rule_id: Optional[str]

    model_config = ConfigDict(from_attributes=True) 