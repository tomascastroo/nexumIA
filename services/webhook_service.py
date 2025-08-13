import hashlib
import hmac
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
from sqlalchemy.orm import Session
from models.DebtPayment import DebtPayment
from models.Debtor import Debtor
from services.error_handling_service import ErrorContext, ErrorSeverity, error_handling_service
from services.validation_service import validation_service

logger = logging.getLogger(__name__)

class PaymentStatus(Enum):
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    EXPIRED = "expired"
    CANCELLED = "cancelled"

@dataclass
class WebhookPayload:
    """Payload estándar para webhooks de pago"""
    external_reference: str
    payment_id: str
    status: PaymentStatus
    amount_paid: Optional[float] = None
    currency: str = "ARS"
    payment_method: Optional[str] = None
    paid_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None
    signature: Optional[str] = None

class WebhookService:
    """Servicio para manejo de webhooks de confirmación de pagos"""
    
    def __init__(self):
        import os
        from dotenv import load_dotenv
        
        load_dotenv()
        
        # Configuración de webhooks por proveedor
        self.providers = {
            'mercadopago': {
                'webhook_url': '/webhook/mercadopago',
                'signature_header': 'x-signature',
                'secret_key': os.getenv('MERCADOPAGO_WEBHOOK_SECRET', 'your_mercadopago_secret'),
                'timeout_seconds': 30
            },
            'stripe': {
                'webhook_url': '/webhook/stripe',
                'signature_header': 'stripe-signature',
                'secret_key': os.getenv('STRIPE_WEBHOOK_SECRET', 'your_stripe_secret'),
                'timeout_seconds': 30
            },
            'mock': {
                'webhook_url': '/webhook/mock',
                'signature_header': 'x-mock-signature',
                'secret_key': os.getenv('MOCK_WEBHOOK_SECRET', 'mock_secret_key'),
                'timeout_seconds': 10
            }
        }
        
        # Estados de pago válidos
        self.valid_statuses = [status.value for status in PaymentStatus]
    
    def validate_webhook_signature(
        self, 
        payload: str, 
        signature: str, 
        provider: str
    ) -> bool:
        """Valida la firma del webhook para prevenir ataques"""
        if provider not in self.providers:
            logger.error(f"Proveedor de pago no soportado: {provider}")
            return False
        
        config = self.providers[provider]
        secret_key = config['secret_key']
        
        try:
            # Calcular firma esperada
            expected_signature = hmac.new(
                secret_key.encode('utf-8'),
                payload.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            # Comparar firmas (timing-safe)
            return hmac.compare_digest(signature, expected_signature)
            
        except Exception as e:
            logger.error(f"Error validando firma del webhook: {e}")
            return False
    
    def parse_webhook_payload(
        self, 
        raw_payload: Dict[str, Any], 
        provider: str
    ) -> Optional[WebhookPayload]:
        """Parsea el payload del webhook según el proveedor"""
        try:
            if provider == 'mercadopago':
                return self._parse_mercadopago_payload(raw_payload)
            elif provider == 'stripe':
                return self._parse_stripe_payload(raw_payload)
            elif provider == 'mock':
                return self._parse_mock_payload(raw_payload)
            else:
                logger.error(f"Proveedor no soportado: {provider}")
                return None
                
        except Exception as e:
            logger.error(f"Error parseando payload del webhook: {e}")
            return None
    
    def _parse_mercadopago_payload(self, payload: Dict[str, Any]) -> WebhookPayload:
        """Parsea payload de MercadoPago"""
        data = payload.get('data', {})
        # Mapear estados de MercadoPago a nuestros PaymentStatus
        raw_status = str(data.get('status', 'pending')).lower()
        status_map = {
            'approved': 'paid',
            'authorized': 'paid',
            'in_process': 'pending',
            'in_mediation': 'pending',
            'rejected': 'failed',
            'cancelled': 'cancelled',
            'refunded': 'failed',
        }
        mapped_status = status_map.get(raw_status, raw_status)

        return WebhookPayload(
            external_reference=data.get('external_reference', ''),
            payment_id=str(data.get('id', '')),
            status=PaymentStatus(mapped_status),
            amount_paid=float(data.get('transaction_amount', 0)),
            currency=data.get('currency_id', 'ARS'),
            payment_method=data.get('payment_method_id'),
            paid_at=(
                datetime.fromisoformat(data.get('date_approved').replace('Z', '+00:00'))
                if data.get('date_approved')
                else None
            ),
            metadata=data.get('metadata', {})
        )
    
    def _parse_stripe_payload(self, payload: Dict[str, Any]) -> WebhookPayload:
        """Parsea payload de Stripe"""
        data = payload.get('data', {}).get('object', {})
        
        return WebhookPayload(
            external_reference=data.get('metadata', {}).get('external_reference', ''),
            payment_id=data.get('id', ''),
            status=PaymentStatus(data.get('status', 'pending')),
            amount_paid=float(data.get('amount', 0)) / 100,  # Stripe usa centavos
            currency=data.get('currency', 'ars'),
            payment_method=data.get('payment_method'),
            paid_at=datetime.fromtimestamp(data.get('created', 0)) if data.get('created') else None,
            metadata=data.get('metadata', {})
        )
    
    def _parse_mock_payload(self, payload: Dict[str, Any]) -> WebhookPayload:
        """Parsea payload de mock para testing"""
        return WebhookPayload(
            external_reference=payload.get('external_reference', ''),
            payment_id=payload.get('payment_id', ''),
            status=PaymentStatus(payload.get('status', 'pending')),
            amount_paid=float(payload.get('amount_paid', 0)),
            currency=payload.get('currency', 'ARS'),
            payment_method=payload.get('payment_method'),
            paid_at=datetime.fromisoformat(payload.get('paid_at', '')) if payload.get('paid_at') else None,
            metadata=payload.get('metadata', {})
        )
    
    def process_payment_webhook(
        self, 
        db: Session, 
        webhook_payload: WebhookPayload,
        provider: str
    ) -> Dict[str, Any]:
        """Procesa un webhook de confirmación de pago"""
        
        # Contexto para logging de errores
        error_context = ErrorContext(
            service="webhook_service",
            operation="process_payment_webhook",
            additional_data={
                'external_reference': webhook_payload.external_reference,
                'payment_id': webhook_payload.payment_id,
                'provider': provider
            }
        )
        
        try:
            # Buscar el pago en la base de datos
            payment = db.query(DebtPayment).filter(
                DebtPayment.external_reference == webhook_payload.external_reference
            ).first()
            
            if payment is None:
                logger.error(f"Pago no encontrado: {webhook_payload.external_reference}")
                error_context.severity = ErrorSeverity.HIGH
                error_handling_service.log_error(
                    Exception(f"Pago no encontrado: {webhook_payload.external_reference}"),
                    error_context
                )
                return {
                    'success': False,
                    'error': 'Payment not found',
                    'external_reference': webhook_payload.external_reference
                }
            
            # Verificar que no sea un webhook duplicado
            if payment.status == webhook_payload.status.value:
                logger.info(f"Webhook duplicado para pago {payment.id}")
                return {
                    'success': True,
                    'message': 'Duplicate webhook',
                    'payment_id': payment.id
                }
            
            # Actualizar estado del pago
            old_status = payment.status
            setattr(payment, 'status', webhook_payload.status.value)
            
            if webhook_payload.amount_paid:
                setattr(payment, 'amount_paid', webhook_payload.amount_paid)
            
            if webhook_payload.paid_at:
                setattr(payment, 'paid_at', webhook_payload.paid_at)
            elif webhook_payload.status == PaymentStatus.PAID:
                setattr(payment, 'paid_at', datetime.utcnow())
            
            # Actualizar estado del deudor si el pago fue exitoso
            if webhook_payload.status == PaymentStatus.PAID:
                debtor = db.query(Debtor).filter(Debtor.id == payment.debtor_id).first()
                if debtor:
                    setattr(debtor, 'state', "VERDE")  # O estado apropiado
                    logger.info(f"Deudor {debtor.id} actualizado a estado VERDE por pago exitoso")
            
            db.commit()
            
            logger.info(f"Pago {payment.id} actualizado: {old_status} -> {payment.status}")
            
            return {
                'success': True,
                'payment_id': payment.id,
                'old_status': old_status,
                'new_status': payment.status,
                'debtor_updated': webhook_payload.status == PaymentStatus.PAID
            }
            
        except Exception as e:
            db.rollback()
            error_context.severity = ErrorSeverity.CRITICAL
            error_handling_service.log_error(e, error_context)
            
            return {
                'success': False,
                'error': str(e),
                'external_reference': webhook_payload.external_reference
            }
    
    def validate_webhook_payload(self, payload: WebhookPayload) -> List[str]:
        """Valida que el payload del webhook sea correcto"""
        errors = []
        
        # Validar campos obligatorios
        if not payload.external_reference:
            errors.append("external_reference es obligatorio")
        
        if not payload.payment_id:
            errors.append("payment_id es obligatorio")
        
        if payload.status.value not in self.valid_statuses:
            errors.append(f"status inválido: {payload.status.value}")
        
        # Validar monto si está presente
        if payload.amount_paid is not None:
            amount_validation = validation_service.validate_amount(payload.amount_paid)
            if not amount_validation.is_valid:
                errors.append(f"amount_paid inválido: {amount_validation.message}")
        
        # Validar fecha si está presente
        if payload.paid_at and payload.paid_at > datetime.utcnow():
            errors.append("paid_at no puede ser en el futuro")
        
        return errors
    
    def get_webhook_config(self, provider: str) -> Optional[Dict[str, Any]]:
        """Obtiene la configuración de webhook para un proveedor"""
        return self.providers.get(provider)
    
    def register_webhook_url(self, provider: str, url: str) -> bool:
        """Registra una URL de webhook para un proveedor"""
        if provider not in self.providers:
            return False
        
        self.providers[provider]['webhook_url'] = url
        return True

# Instancia global del servicio
webhook_service = WebhookService() 