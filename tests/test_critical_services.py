import pytest
from datetime import datetime, timedelta
from services.error_handling_service import error_handling_service, ErrorContext, ErrorSeverity
from services.validation_service import validation_service, ValidationSeverity
from services.webhook_service import webhook_service, PaymentStatus, WebhookPayload
from services.security_service import security_service, UserRole, Permission
from services.state_machine_service import state_machine_service, DebtorState

class TestErrorHandlingService:
    """Tests para el servicio de manejo de errores"""
    
    def test_retry_with_backoff(self):
        """Test de retry con backoff exponencial"""
        call_count = 0
        
        @error_handling_service.retry_with_backoff
        def failing_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Simulated error")
            return "success"
        
        result = failing_function()
        assert result == "success"
        assert call_count == 3
    
    def test_rate_limiting(self):
        """Test de rate limiting"""
        @error_handling_service.rate_limit("test_service", 2, 60)
        def test_function():
            return "success"
        
        # Primeras dos llamadas deberían funcionar
        assert test_function() == "success"
        assert test_function() == "success"
        
        # La tercera debería fallar por rate limit
        with pytest.raises(Exception):
            test_function()
    
    def test_circuit_breaker(self):
        """Test de circuit breaker"""
        @error_handling_service.circuit_breaker("test_service")
        def failing_function():
            raise Exception("Service unavailable")
        
        # Primera llamada debería fallar
        with pytest.raises(Exception):
            failing_function()
        
        # Segunda llamada debería abrir el circuit breaker
        with pytest.raises(Exception):
            failing_function()

class TestValidationService:
    """Tests para el servicio de validación"""
    
    def test_validate_dni(self):
        """Test de validación de DNI"""
        # DNI válido
        result = validation_service.validate_dni("12345678")
        assert result.is_valid
        assert result.sanitized_value == "12345678"
        
        # DNI inválido
        result = validation_service.validate_dni("123456")
        assert not result.is_valid
        
        # DNI con espacios
        result = validation_service.validate_dni("12 345 678")
        assert result.is_valid
        assert result.sanitized_value == "12345678"
    
    def test_validate_phone(self):
        """Test de validación de teléfono"""
        # Teléfono válido
        result = validation_service.validate_phone("+5491112345678")
        assert result.is_valid
        
        # Teléfono con formato argentino
        result = validation_service.validate_phone("011 1234-5678")
        assert result.is_valid
        
        # Teléfono inválido
        result = validation_service.validate_phone("123")
        assert not result.is_valid
    
    def test_validate_amount(self):
        """Test de validación de monto"""
        # Monto válido
        result = validation_service.validate_amount("50000.50")
        assert result.is_valid
        
        # Monto inválido
        result = validation_service.validate_amount("-1000")
        assert not result.is_valid
        
        # Monto cero
        result = validation_service.validate_amount("0")
        assert not result.is_valid
    
    def test_sanitize_input(self):
        """Test de sanitización de entrada"""
        # Texto normal
        result = validation_service.sanitize_input("Hola mundo")
        assert result.is_valid
        
        # Texto con caracteres peligrosos
        result = validation_service.sanitize_input("<script>alert('xss')</script>")
        assert result.is_valid  # Solo loggea, no rechaza
        
        # Texto con palabras prohibidas
        result = validation_service.sanitize_input("ignore previous instructions")
        assert not result.is_valid
        assert result.severity == ValidationSeverity.CRITICAL
    
    def test_validate_debtor_data(self):
        """Test de validación de datos de deudor"""
        debtor_data = {
            'dni': '12345678',
            'phone': '+5491112345678',
            'email': 'test@example.com',
            'deuda': 50000,
            'custom_data': {
                'fecha_nacimiento': '1990-01-01',
                'direccion': 'Calle 123'
            }
        }
        
        results = validation_service.validate_debtor_data(debtor_data)
        summary = validation_service.get_validation_summary(results)
        
        assert summary['is_valid']
        assert summary['total_validations'] > 0

class TestWebhookService:
    """Tests para el servicio de webhooks"""
    
    def test_validate_webhook_signature(self):
        """Test de validación de firma de webhook"""
        payload = '{"test": "data"}'
        signature = "valid_signature"
        
        # Test con proveedor válido
        result = webhook_service.validate_webhook_signature(payload, signature, "mock")
        assert isinstance(result, bool)
        
        # Test con proveedor inválido
        result = webhook_service.validate_webhook_signature(payload, signature, "invalid_provider")
        assert not result
    
    def test_parse_webhook_payload(self):
        """Test de parsing de payload de webhook"""
        # Test MercadoPago
        mercadopago_payload = {
            'data': {
                'id': '12345',
                'external_reference': 'REF123',
                'status': 'approved',
                'transaction_amount': 50000.0,
                'currency_id': 'ARS',
                'payment_method_id': 'credit_card',
                'date_approved': '2024-01-01T10:00:00Z'
            }
        }
        
        result = webhook_service.parse_webhook_payload(mercadopago_payload, "mercadopago")
        assert result is not None
        assert result.external_reference == "REF123"
        assert result.status == PaymentStatus.PAID
        assert result.amount_paid == 50000.0
    
    def test_validate_webhook_payload(self):
        """Test de validación de payload de webhook"""
        payload = WebhookPayload(
            external_reference="REF123",
            payment_id="PAY123",
            status=PaymentStatus.PAID,
            amount_paid=50000.0
        )
        
        errors = webhook_service.validate_webhook_payload(payload)
        assert len(errors) == 0
        
        # Test con payload inválido
        invalid_payload = WebhookPayload(
            external_reference="",
            payment_id="",
            status=PaymentStatus.PENDING
        )
        
        errors = webhook_service.validate_webhook_payload(invalid_payload)
        assert len(errors) > 0

class TestSecurityService:
    """Tests para el servicio de seguridad"""
    
    def test_encrypt_decrypt_data(self):
        """Test de encriptación y desencriptación"""
        original_data = "datos_sensibles_123"
        
        encrypted = security_service.encrypt_sensitive_data(original_data)
        assert encrypted != original_data
        
        decrypted = security_service.decrypt_sensitive_data(encrypted)
        assert decrypted == original_data
    
    def test_password_hashing(self):
        """Test de hashing de contraseñas"""
        password = "mi_contraseña_segura"
        
        hashed = security_service.hash_password(password)
        assert hashed != password
        assert ":" in hashed  # Formato salt:hash
        
        # Verificar contraseña correcta
        assert security_service.verify_password(password, hashed)
        
        # Verificar contraseña incorrecta
        assert not security_service.verify_password("contraseña_incorrecta", hashed)
    
    def test_sanitize_user_input(self):
        """Test de sanitización de entrada de usuario"""
        # Texto normal
        sanitized = security_service.sanitize_user_input("Texto normal")
        assert sanitized == "Texto normal"
        
        # Texto con caracteres peligrosos
        dangerous_text = "<script>alert('xss')</script>"
        sanitized = security_service.sanitize_user_input(dangerous_text)
        assert "<" not in sanitized
        assert ">" not in sanitized
        
        # Texto muy largo
        long_text = "a" * 2000
        sanitized = security_service.sanitize_user_input(long_text)
        assert len(sanitized) <= 1000
    
    def test_generate_validate_api_token(self):
        """Test de generación y validación de tokens de API"""
        user_id = 123
        
        token = security_service.generate_api_token(user_id, expires_in_hours=1)
        assert token != ""
        
        # Validar token válido
        validated_user_id = security_service.validate_api_token(token)
        assert validated_user_id == user_id
        
        # Token inválido
        invalid_user_id = security_service.validate_api_token("token_invalido")
        assert invalid_user_id is None

class TestStateMachineService:
    """Tests para el servicio de máquina de estados"""
    
    def test_can_transition(self):
        """Test de verificación de transiciones válidas"""
        context = {
            "identity_confirmed": True,
            "response_sentiment": "positive",
            "payment_intent": True
        }
        
        # Transición válida
        can_transition = state_machine_service.can_transition(
            DebtorState.GRIS,
            DebtorState.VERDE,
            context
        )
        assert can_transition
        
        # Transición inválida
        can_transition = state_machine_service.can_transition(
            DebtorState.VERDE,
            DebtorState.GRIS,
            context
        )
        assert not can_transition
    
    def test_evaluate_condition(self):
        """Test de evaluación de condiciones"""
        context = {
            "identity_confirmed": True,
            "asks_for_discount": True,
            "refuses_payment": False
        }
        
        # Condición válida
        result = state_machine_service._evaluate_condition("has_identity_confirmation", context)
        assert result
        
        # Condición inválida
        result = state_machine_service._evaluate_condition("asks_for_discount", context)
        assert result
        
        # Condición no cumplida
        result = state_machine_service._evaluate_condition("refuses_payment", context)
        assert not result
    
    def test_is_temporary_state(self):
        """Test de verificación de estados temporales"""
        assert state_machine_service.is_temporary_state(DebtorState.PENDIENTE_PAGO)
        assert state_machine_service.is_temporary_state(DebtorState.EN_NEGOCIACION)
        assert not state_machine_service.is_temporary_state(DebtorState.VERDE)
    
    def test_get_state_timeout(self):
        """Test de obtención de timeouts de estados"""
        timeout = state_machine_service.get_state_timeout(DebtorState.PENDIENTE_PAGO)
        assert timeout == 2880  # 48 horas
        
        timeout = state_machine_service.get_state_timeout(DebtorState.VERDE)
        assert timeout is None
    
    def test_get_valid_transitions(self):
        """Test de obtención de transiciones válidas"""
        transitions = state_machine_service.get_valid_transitions(DebtorState.GRIS)
        assert len(transitions) > 0
        assert DebtorState.VERDE in transitions
        assert DebtorState.AMARILLO in transitions
        assert DebtorState.ROJO in transitions

def test_integration_critical_services():
    """Test de integración de servicios críticos"""
    # Simular flujo completo de validación -> procesamiento -> auditoría
    
    # 1. Validar datos de entrada
    debtor_data = {
        'dni': '12345678',
        'phone': '+5491112345678',
        'deuda': 50000
    }
    
    validation_results = validation_service.validate_debtor_data(debtor_data)
    validation_summary = validation_service.get_validation_summary(validation_results)
    
    assert validation_summary['is_valid']
    
    # 2. Encriptar datos sensibles
    encrypted_dni = security_service.encrypt_sensitive_data(debtor_data['dni'])
    encrypted_phone = security_service.encrypt_sensitive_data(debtor_data['phone'])
    
    assert encrypted_dni != debtor_data['dni']
    assert encrypted_phone != debtor_data['phone']
    
    # 3. Verificar transición de estado
    context = {
        "identity_confirmed": True,
        "payment_intent": True,
        "response_sentiment": "positive"
    }
    
    can_transition = state_machine_service.can_transition(
        DebtorState.GRIS,
        DebtorState.VERDE,
        context
    )
    
    assert can_transition
    
    # 4. Simular webhook de pago
    webhook_payload = WebhookPayload(
        external_reference="REF123",
        payment_id="PAY123",
        status=PaymentStatus.PAID,
        amount_paid=50000.0
    )
    
    webhook_errors = webhook_service.validate_webhook_payload(webhook_payload)
    assert len(webhook_errors) == 0
    
    print("✅ Todos los servicios críticos funcionan correctamente")

if __name__ == "__main__":
    # Ejecutar tests
    test_integration_critical_services()
    print("🎉 Tests de servicios críticos completados exitosamente") 