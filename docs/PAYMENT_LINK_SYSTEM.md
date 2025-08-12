# Sistema de Links de Pago - Nexum IA

## 🎯 Objetivo

Implementar un sistema inteligente de generación de links de pago que respete las reglas específicas de cobranza según el estado del deudor, priorizando la conversión de conversaciones en pagos de manera profesional y empática.

## 🧩 Reglas Implementadas

### 1. Validación de Identidad
- **NUNCA** se genera un link de pago si el deudor no validó su identidad
- Campos requeridos: DNI, email, u otros datos de identificación
- Se verifica en el historial de conversación y datos del deudor

### 2. Estados del Deudor

#### 🟢 VERDE
- **Acción**: Generar link inmediatamente si lo solicita
- **Respuesta**: "Claro, puedo generarte un link de pago inmediato. Tené en cuenta que vence en 48 hs."
- **Link**: Se genera automáticamente con vencimiento de 48 horas

#### 🟡 AMARILLO
- **Acción**: Solo generar link si lo solicita explícitamente
- **Respuesta**: "¿Querés que te envíe el link para pagar?"
- **Link**: Se genera solo ante solicitud explícita

#### 🔴 ROJO
- **Acción**: NO generar link automáticamente
- **Respuesta**: "Entiendo tu situación. Un especialista se pondrá en contacto contigo."
- **Intervención**: Requiere intervención humana

#### ⚪ GRIS
- **Acción**: NO generar link automáticamente
- **Respuesta**: "Gracias por tu interés. Un especialista se pondrá en contacto contigo."
- **Intervención**: Requiere intervención humana

## 🏗️ Arquitectura del Sistema

### Backend

#### 1. `PaymentLinkService` (`services/payment_link_service.py`)
```python
class PaymentLinkService:
    - should_generate_payment_link(): Evalúa si debe generar link
    - generate_payment_link_response(): Genera respuesta apropiada
    - create_payment_link(): Crea link de pago real/simulado
    - _check_identity_validation(): Verifica validación de identidad
    - _detect_payment_link_request(): Detecta solicitud de link
```

#### 2. Integración en `ConversationService`
```python
# Verificación antes de procesar con LLM
should_generate_link, reason, link_data = payment_link_service.should_generate_payment_link(
    user_message=body,
    debtor_state=new_state,
    conversation_history=current_history,
    debtor_data=current_custom_data
)
```

#### 3. Endpoints REST
- `POST /debt_payment/check-eligibility/{debtor_id}`: Verifica elegibilidad
- `POST /debt_payment/generate`: Genera link de pago
- `GET /debt_payment/history/{debtor_id}`: Historial de pagos

### Frontend

#### 1. `PaymentLinkService` (`services/paymentLinkService.ts`)
```typescript
class PaymentLinkService:
    - checkEligibility(): Verifica elegibilidad
    - generatePaymentLink(): Genera link
    - getPaymentHistory(): Obtiene historial
    - analyzePaymentLinkRequest(): Analiza solicitud
    - generateResponseByState(): Genera respuesta por estado
```

#### 2. Componente `PaymentHistory`
- Muestra historial de pagos del deudor
- Estados visuales: Pagado, Pendiente, Fallido, Expirado
- Formato de moneda y fechas

## 🔍 Detección de Solicitudes

### Palabras Clave para Links de Pago
```python
payment_link_keywords = [
    "link de pago", "link para pagar", "enlace de pago",
    "pagar", "quiero pagar", "dame el link", "envíame el link",
    "cómo pago", "donde pago", "pago online", "transferencia",
    "débito", "crédito", "tarjeta", "mercadopago", "paypal", "stripe"
]
```

### Palabras Clave para Validación de Identidad
```python
identity_validation_keywords = [
    "dni", "documento", "identidad", "validar", "confirmar",
    "email", "correo", "datos", "información personal"
]
```

## 📊 Flujo de Procesamiento

### 1. Recepción de Mensaje
```
Usuario envía mensaje → Webhook → ConversationService
```

### 2. Análisis de Estado
```
ConversationService → update_state() → classify_state()
```

### 3. Verificación de Link de Pago
```
ConversationService → PaymentLinkService.should_generate_payment_link()
```

### 4. Generación de Respuesta
```
Si debe generar → PaymentLinkService.generate_payment_link_response()
Si no debe generar → LLM con reglas específicas
```

### 5. Almacenamiento
```
Respuesta → conversation_history → Database
Link → DebtPayment table → Database
```

## 🎨 Respuestas Sugeridas

### Estado VERDE
```
"Gracias por tu predisposición. Enseguida te comparto el link para regularizar la deuda.

Tu deuda es de $50,000 y el link vence en 48 horas.

Link de pago: [GENERAR_LINK_AQUI]

Recordá que el link vence en 48 horas. Si tenés alguna consulta, no dudes en preguntarme."
```

### Estado AMARILLO
```
"Entiendo tu situación. ¿Querés que te envíe el link con el descuento vigente?

Tu deuda es de $50,000 y tenemos opciones de descuento disponibles.

¿Querés que te lo envíe ahora mismo por este medio?"
```

### Estados ROJO/GRIS
```
"Entiendo tu situación. Un especialista se pondrá en contacto contigo para ayudarte."
```

## 🔧 Configuración

### Variables de Entorno
```bash
# Configuración de pagos
PAYMENT_LINK_EXPIRY_HOURS=48
PAYMENT_METHOD=mock  # mock, mercadopago, stripe
```

### Base de Datos
```sql
-- Tabla de pagos
CREATE TABLE debt_payments (
    id INTEGER PRIMARY KEY,
    debtor_id INTEGER NOT NULL,
    amount_requested FLOAT NOT NULL,
    payment_link VARCHAR,
    status VARCHAR DEFAULT 'pending',
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);
```

## 🚀 Uso

### Verificar Elegibilidad
```typescript
const eligibility = await paymentLinkService.checkEligibility(
    debtorId, 
    "Quiero pagar mi deuda"
);
```

### Generar Link de Pago
```typescript
const payment = await paymentLinkService.generatePaymentLink({
    debtor_id: 123,
    amount_requested: 50000,
    discount_applied: 10,
    method: "mock"
});
```

### Obtener Historial
```typescript
const history = await paymentLinkService.getPaymentHistory(debtorId);
```

## 📈 Métricas y Analytics

### Trazabilidad
- Cada decisión de link se registra en `traceability_service`
- Se guarda el estado del deudor, razón de decisión, y respuesta generada
- Permite análisis de efectividad por estado y tipo de solicitud

### KPIs Sugeridos
- Tasa de conversión por estado del deudor
- Tiempo promedio hasta solicitud de link
- Efectividad de respuestas por estado
- Tasa de pago por link generado

## 🔒 Seguridad

### Validaciones
- Verificación de identidad antes de generar links
- Validación de estado del deudor
- Control de acceso por token JWT
- Sanitización de inputs

### Auditoría
- Log de todas las decisiones de generación de links
- Historial completo de pagos
- Trazabilidad de conversaciones

## 🎯 Próximos Pasos

1. **Integración con Proveedores Reales**
   - MercadoPago
   - Stripe
   - PayPal

2. **Mejoras en IA**
   - Análisis de sentimiento más avanzado
   - Predicción de probabilidad de pago
   - Personalización de respuestas

3. **Analytics Avanzados**
   - Dashboard de métricas
   - Reportes de efectividad
   - Optimización automática de respuestas

4. **Funcionalidades Adicionales**
   - Links de pago con descuentos dinámicos
   - Planes de pago personalizados
   - Recordatorios automáticos 