# Error Handling Service

## 🧠 Descripción general
Servicio centralizado para manejo robusto de errores, retries con backoff exponencial, rate limiting y circuit breakers. Proporciona resiliencia y confiabilidad al sistema ante fallos de servicios externos como OpenAI, pasarelas de pago y APIs de WhatsApp.

## ⚙️ Funcionalidades principales
- **Retry con backoff exponencial**: Reintentos automáticos con espera progresiva (1s, 2s, 4s, 8s...)
- **Rate limiting**: Control de frecuencia de llamadas por servicio (ej: 100 requests/minuto)
- **Circuit breaker**: Prevención de cascada de fallos cuando un servicio está caído
- **Logging estructurado**: Registro contextual de errores con metadata
- **Decorators de conveniencia**: `@retry_on_failure`, `@rate_limited`, `@circuit_breaker_protected`
- **Fallback responses**: Respuestas predefinidas cuando fallan servicios críticos

## 🔐 Consideraciones de seguridad
- **Logging seguro**: No expone datos sensibles (DNI, teléfonos, montos) en logs
- **Contexto de errores**: Incluye información para debugging sin comprometer seguridad
- **Rate limiting**: Previene ataques de denegación de servicio (DDoS)
- **Circuit breaker**: Evita sobrecarga de servicios externos en fallo

## ⚠️ Errores posibles y manejo
- **OpenAI API errors**: 
  - Rate limits: Espera automática y reintento
  - Timeouts: Retry con backoff exponencial
  - Service unavailable: Circuit breaker activado
- **Pasarelas de pago**:
  - Network errors: Retry hasta 3 veces
  - Invalid responses: Fallback con respuesta de error
- **WhatsApp API**:
  - Message delivery failures: Logging y reintento
  - Rate limits: Espera y reintento automático

## 📡 Integraciones externas
- **OpenAI API**: Manejo de rate limits (3 requests/minuto) y timeouts (30s)
- **MercadoPago**: Retry en fallos de confirmación de pagos
- **Stripe**: Manejo de errores de webhooks y confirmaciones
- **WhatsApp Business API**: Retry en fallos de envío de mensajes

## 📊 Logs y métricas
- **Error logs**: Con contexto completo (usuario, operación, datos adicionales)
- **Retry metrics**: Número de reintentos por operación y servicio
- **Circuit breaker status**: Estado de circuit breakers por servicio (OPEN/CLOSED/HALF_OPEN)
- **Rate limit hits**: Cuándo se activan rate limits y qué servicios
- **Response times**: Tiempos de respuesta por servicio externo

## 🧪 Tests y validaciones
- ✅ **Tests de retry**: Verificación de backoff exponencial y límites
- ✅ **Tests de rate limiting**: Control de frecuencia y bloqueos
- ✅ **Tests de circuit breaker**: Prevención de cascada de fallos
- ✅ **Tests de logging**: Verificación de contexto y seguridad
- ⚠️ **Pendiente**: Tests de integración con servicios externos reales
- ⚠️ **Pendiente**: Métricas de performance en producción

## 📋 Uso en el proyecto

### Decorator básico
```python
from services.error_handling_service import retry_on_failure

@retry_on_failure(max_retries=3)
def call_openai_api(prompt):
    # Tu código aquí
    pass
```

### Rate limiting
```python
from services.error_handling_service import rate_limited

@rate_limited("openai", max_requests=100, window_seconds=60)
def generate_response(prompt):
    # Tu código aquí
    pass
```

### Circuit breaker
```python
from services.error_handling_service import circuit_breaker_protected

@circuit_breaker_protected("payment_gateway")
def process_payment(payment_data):
    # Tu código aquí
    pass
```

## 🔧 Configuración

### Variables de entorno
```bash
# Configuración de retries
MAX_RETRIES=3
BACKOFF_FACTOR=2
MAX_BACKOFF=60

# Configuración de rate limiting
DEFAULT_RATE_LIMIT=100
DEFAULT_WINDOW_SECONDS=60

# Configuración de circuit breaker
CIRCUIT_BREAKER_THRESHOLD=5
CIRCUIT_BREAKER_TIMEOUT=60
```

### Configuración por servicio
```python
# OpenAI
OPENAI_RATE_LIMIT = 3  # requests per minute
OPENAI_TIMEOUT = 30    # seconds

# MercadoPago
MERCADOPAGO_RATE_LIMIT = 100  # requests per minute
MERCADOPAGO_TIMEOUT = 10       # seconds

# WhatsApp
WHATSAPP_RATE_LIMIT = 50   # messages per minute
WHATSAPP_TIMEOUT = 15       # seconds
```

## 📈 Monitoreo recomendado

### Alertas críticas
- Circuit breakers abiertos por más de 5 minutos
- Rate limits alcanzados consistentemente
- Tiempo de respuesta promedio > 10 segundos
- Error rate > 5% en cualquier servicio

### Métricas importantes
- **Availability**: % de tiempo que los servicios están disponibles
- **Response time**: P95 y P99 de tiempos de respuesta
- **Error rate**: % de errores por servicio
- **Retry rate**: % de requests que requieren retry
- **Circuit breaker status**: Tiempo en cada estado

## 🚀 Próximas mejoras
1. **Métricas en tiempo real**: Dashboard con Grafana/Prometheus
2. **Alertas automáticas**: Notificaciones por Slack/Email
3. **Auto-scaling**: Ajuste automático de rate limits según carga
4. **Distributed tracing**: Trazabilidad completa de requests
5. **Chaos engineering**: Tests de resiliencia automatizados 