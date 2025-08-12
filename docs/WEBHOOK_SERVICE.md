# Webhook Service

## 🧠 Descripción general
Servicio para procesamiento seguro de webhooks de confirmación de pagos. Valida firmas, parsea payloads de diferentes proveedores (MercadoPago, Stripe) y actualiza estados automáticamente. Es crítico para la sincronización de pagos.

## ⚙️ Funcionalidades principales
- **Validación de firmas**: HMAC-SHA256 para autenticidad de webhooks
- **Parsing de payloads**: Soporte para MercadoPago, Stripe y Mock
- **Procesamiento de pagos**: Actualización automática de estados de deudores
- **Prevención de duplicados**: Control de webhooks repetidos
- **Configuración por proveedor**: Diferentes secretos y formatos
- **Rollback automático**: Manejo de errores en procesamiento

## 🔐 Consideraciones de seguridad
- **Validación de firmas**: Prevención de webhooks falsos o maliciosos
- **Sanitización de payloads**: Limpieza de datos recibidos
- **Validación de datos**: Verificación de campos obligatorios
- **Logging seguro**: No expone secretos o datos sensibles en logs
- **Rate limiting**: Prevención de spam de webhooks

## ⚠️ Errores posibles y manejo
- **Firma inválida**: Rechazo inmediato del webhook con logging
- **Pago no encontrado**: Logging de error y respuesta apropiada
- **Payload malformado**: Validación y logging de errores
- **Webhook duplicado**: Respuesta exitosa sin procesamiento
- **Error de base de datos**: Rollback automático y logging crítico
- **Timeout de procesamiento**: Manejo de timeouts con retry

## 📡 Integraciones externas
- **MercadoPago**: Webhooks de confirmación de pagos
- **Stripe**: Webhooks de eventos de pago
- **Mock provider**: Para testing y desarrollo
- **Base de datos**: Actualización de estados de pagos y deudores

## 📊 Logs y métricas
- **Webhook processing**: Logs de procesamiento con contexto completo
- **Signature validation**: Métricas de validación de firmas
- **Payment updates**: Registro de actualizaciones de pagos
- **Error rates**: Tasa de errores por proveedor y tipo
- **Processing times**: Tiempos de procesamiento de webhooks
- **Duplicate detection**: Métricas de webhooks duplicados

## 🧪 Tests y validaciones
- ✅ **Tests de validación de firma**: Verificación de HMAC-SHA256
- ✅ **Tests de parsing**: Payloads de MercadoPago y Stripe
- ✅ **Tests de duplicados**: Prevención de webhooks repetidos
- ✅ **Tests de errores**: Manejo de payloads malformados
- ✅ **Tests de rollback**: Recuperación ante errores de DB
- ⚠️ **Pendiente**: Tests de integración con proveedores reales
- ⚠️ **Pendiente**: Tests de performance con alta concurrencia

## 📋 Uso en el proyecto

### Configuración de proveedores
```python
from services.webhook_service import webhook_service

# Configurar MercadoPago
webhook_service.register_webhook_url("mercadopago", "/webhook/mercadopago")

# Configurar Stripe
webhook_service.register_webhook_url("stripe", "/webhook/stripe")
```

### Procesamiento de webhook
```python
from services.webhook_service import webhook_service, PaymentStatus

# Validar firma
is_valid = webhook_service.validate_webhook_signature(
    payload=raw_payload,
    signature=signature_header,
    provider="mercadopago"
)

if is_valid:
    # Parsear payload
    webhook_payload = webhook_service.parse_webhook_payload(
        raw_payload, 
        "mercadopago"
    )
    
    if webhook_payload:
        # Procesar webhook
        result = webhook_service.process_payment_webhook(
            db=db_session,
            webhook_payload=webhook_payload,
            provider="mercadopago"
        )
        
        if result['success']:
            print(f"Pago procesado: {result['payment_id']}")
        else:
            print(f"Error: {result['error']}")
```

### Validación de payload
```python
# Validar payload antes de procesar
errors = webhook_service.validate_webhook_payload(webhook_payload)

if len(errors) == 0:
    # Procesar webhook
    pass
else:
    # Loggear errores de validación
    for error in errors:
        logger.error(f"Error de validación: {error}")
```

## 🔧 Configuración

### Variables de entorno
```bash
# MercadoPago
MERCADOPAGO_WEBHOOK_SECRET=your_mercadopago_secret
MERCADOPAGO_WEBHOOK_URL=/webhook/mercadopago

# Stripe
STRIPE_WEBHOOK_SECRET=your_stripe_secret
STRIPE_WEBHOOK_URL=/webhook/stripe

# Configuración general
WEBHOOK_TIMEOUT=30
WEBHOOK_MAX_RETRIES=3
```

### Configuración por proveedor
```python
PROVIDER_CONFIG = {
    'mercadopago': {
        'webhook_url': '/webhook/mercadopago',
        'signature_header': 'x-signature',
        'secret_key': 'your_mercadopago_secret',
        'timeout_seconds': 30
    },
    'stripe': {
        'webhook_url': '/webhook/stripe',
        'signature_header': 'stripe-signature',
        'secret_key': 'your_stripe_secret',
        'timeout_seconds': 30
    },
    'mock': {
        'webhook_url': '/webhook/mock',
        'signature_header': 'x-mock-signature',
        'secret_key': 'mock_secret_key',
        'timeout_seconds': 10
    }
}
```

## 📈 Monitoreo recomendado

### Alertas críticas
- Webhooks con firma inválida
- Pagos no encontrados en base de datos
- Tasa de errores de procesamiento > 5%
- Tiempo de procesamiento > 10 segundos
- Webhooks duplicados > 10% del total

### Métricas importantes
- **Webhook success rate**: % de webhooks procesados exitosamente
- **Processing time**: P95 y P99 de tiempos de procesamiento
- **Error distribution**: Tipos de errores más comunes
- **Provider performance**: Métricas por proveedor de pago
- **Duplicate rate**: % de webhooks duplicados

## 🚀 Próximas mejoras
1. **Webhook retry**: Reintento automático de webhooks fallidos
2. **Async processing**: Procesamiento asíncrono para alta concurrencia
3. **Webhook queuing**: Cola de webhooks para procesamiento ordenado
4. **Real-time notifications**: Notificaciones en tiempo real de pagos
5. **Webhook analytics**: Dashboard de métricas de webhooks
6. **Multi-tenant support**: Soporte para múltiples cuentas

## 🔒 Seguridad avanzada

### Validación de firmas
```python
def validate_signature(payload: str, signature: str, secret: str) -> bool:
    """Valida firma HMAC-SHA256"""
    expected_signature = hmac.new(
        secret.encode('utf-8'),
        payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(signature, expected_signature)
```

### Prevención de ataques
- **Replay attacks**: Validación de timestamps
- **Signature forgery**: Uso de HMAC-SHA256
- **Data tampering**: Validación de integridad
- **Rate limiting**: Control de frecuencia de webhooks
- **IP whitelisting**: Restricción por IP de proveedores

### Auditoría
- **Webhook audit log**: Registro completo de todos los webhooks
- **Signature validation log**: Logs de validación de firmas
- **Payment update log**: Registro de actualizaciones de pagos
- **Error tracking**: Seguimiento de errores por proveedor 