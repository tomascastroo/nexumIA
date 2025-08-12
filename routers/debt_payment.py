from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from models.DebtPayment import DebtPayment
from models.Debtor import Debtor
from schemas.debt_payment import DebtPaymentIn, DebtPaymentOut, PaymentRequest
from services.payment_link_service import payment_link_service
from typing import List, Optional, Dict, Any, cast
from datetime import datetime, timedelta

# Agregar get_db aquí
from db.db import SessionLocal
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import inspect
from db.db import engine

inspector = inspect(engine)
print('debt_payments' in inspector.get_table_names())  # Debe imprimir True

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

router = APIRouter(prefix="/debt_payment", tags=["debt_payment"])

# Endpoint: Generar link de pago (mock)
@router.post("/generate", response_model=DebtPaymentOut)
def generate_payment_link(request: PaymentRequest, db: Session = Depends(get_db)):
    debtor = db.query(Debtor).filter(Debtor.id == request.debtor_id).first()
    if not debtor:
        raise HTTPException(status_code=404, detail="Debtor not found")
    
    # Verificar estado del deudor
    if debtor.state in ["ROJO", "GRIS"]:
        raise HTTPException(
            status_code=400, 
            detail=f"No se puede generar link de pago para deudor en estado {debtor.state}"
        )
    
    # Simular generación de link de pago externo
    payment_link = f"https://mockpay.com/pay/{request.debtor_id}/{int(datetime.utcnow().timestamp())}"
    external_reference = f"mock-{request.debtor_id}-{int(datetime.utcnow().timestamp())}"
    expires_at = datetime.utcnow() + timedelta(hours=48)  # 48 horas como especificado
    
    payment = DebtPayment(
        debtor_id=request.debtor_id,
        amount_requested=request.amount_requested,
        discount_applied=request.discount_applied,
        status="pending",
        payment_link=payment_link,
        method=request.method,
        external_reference=external_reference,
        created_at=datetime.utcnow(),
        expires_at=expires_at,
        campaign_id=request.campaign_id,
        rule_id=request.rule_id
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return payment

# Endpoint: Confirmar pago manual
@router.post("/confirm", response_model=DebtPaymentOut)
def confirm_payment(payment_id: int, amount_paid: float, db: Session = Depends(get_db)):
    payment = db.query(DebtPayment).filter(DebtPayment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    setattr(payment, "status", "paid")
    setattr(payment, "amount_paid", amount_paid)
    setattr(payment, "paid_at", datetime.utcnow())
    db.commit()
    db.refresh(payment)
    # Actualizar estado del deudor
    debtor = db.query(Debtor).filter(Debtor.id == payment.debtor_id).first()
    if debtor:
        setattr(debtor, "state", "VERDE")  # O "PAGADO" si tienes ese estado
        db.commit()
    return payment

# Endpoint: Webhook de pago (mock)
@router.post("/webhook")
def payment_webhook(payload: dict, db: Session = Depends(get_db)):
    external_reference = payload.get("external_reference")
    status = payload.get("status")
    amount_paid = payload.get("amount_paid")
    payment = db.query(DebtPayment).filter(DebtPayment.external_reference == external_reference).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    if status == "paid":
        setattr(payment, "status", "paid")
        setattr(payment, "amount_paid", amount_paid)
        setattr(payment, "paid_at", datetime.utcnow())
        # Actualizar estado del deudor
        debtor = db.query(Debtor).filter(Debtor.id == payment.debtor_id).first()
        if debtor:
            setattr(debtor, "state", "VERDE")
            db.commit()
    elif status == "failed":
        setattr(payment, "status", "failed")
        db.commit()
    return {"ok": True}

# Endpoint: Verificar elegibilidad para link de pago
@router.post("/check-eligibility/{debtor_id}")
def check_payment_link_eligibility(
    debtor_id: int, 
    user_message: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Verifica si un deudor puede recibir un link de pago según las reglas.
    """
    debtor = db.query(Debtor).filter(Debtor.id == debtor_id).first()
    if not debtor:
        raise HTTPException(status_code=404, detail="Debtor not found")
    
    # Obtener historial de conversación
    conversation_history: List[Dict[str, str]] = []
    if debtor.conversation_history is not None:
        try:
            import json
            if isinstance(debtor.conversation_history, str):
                conversation_history = json.loads(debtor.conversation_history)
            else:
                conversation_history = cast(List[Dict[str, str]], debtor.conversation_history)
        except:
            conversation_history = []
    
    # Verificar elegibilidad usando el servicio
    should_generate, reason, data = payment_link_service.should_generate_payment_link(
        user_message=user_message,
        debtor_state=str(debtor.state),
        conversation_history=conversation_history,
        debtor_data=cast(Dict[str, Any], debtor.custom_data) if debtor.custom_data is not None else {}
    )
    
    return {
        "debtor_id": debtor_id,
        "debtor_state": debtor.state,
        "should_generate": should_generate,
        "reason": reason,
        "data": data,
        "message": data.get("message", "")
    }

# Endpoint: Historial de pagos de un deudor
@router.get("/history/{debtor_id}", response_model=List[DebtPaymentOut])
def get_payment_history(debtor_id: int, db: Session = Depends(get_db)):
    payments = db.query(DebtPayment).filter(DebtPayment.debtor_id == debtor_id).order_by(DebtPayment.created_at.desc()).all()
    return payments 