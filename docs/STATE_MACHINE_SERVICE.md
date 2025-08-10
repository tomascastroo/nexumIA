# State Machine Service

## 🧠 Descripción general
Servicio de máquina de estados robusta para gestión de estados de deudores. Maneja transiciones validadas, estados temporales con timeouts, rollback automático y estados compuestos. Es fundamental para la lógica de negocio del sistema de cobranzas.

## ⚙️ Funcionalidades principales
- **Estados base**: VERDE, AMARILLO, ROJO, GRIS
- **Estados temporales**: PENDIENTE_PAGO, EN_NEGOCIACION, ESCALADO_HUMANO
- **Estados compuestos**: VERDE_CON_DESCUENTO, AMARILLO_NEGOCIANDO
- **Transiciones validadas**: Verificación de condiciones antes de cambiar estado
- **Timeouts automáticos**: Rollback de estados temporales
- **Historial de cambios**: Registro completo de transiciones
- **Acciones automáticas**: Ejecución de acciones al cambiar estado

## 🔐 Consideraciones de seguridad
- **Validación de transiciones**: Prevención de cambios de estado no autorizados
- **Auditoría de cambios**: Registro de quién y cuándo cambió el estado
- **Rollback seguro**: Recuperación ante errores en transiciones
- **Contexto de cambios**: Información completa para debugging
- **Prevención de loops**: Detección de transiciones cíclicas

## ⚠️ Errores posibles y manejo
- **Transición inválida**: Rechazo con logging de intento
- **Condiciones no cumplidas**: Validación antes de transición
- **Error en acciones**: Rollback automático del estado
- **Timeout de estado**: Rollback a estado anterior
- **Estado corrupto**: Recuperación desde último estado válido

## 📡 Integraciones externas
- **Base de datos**: Actualización de estados de deudores
- **Payment Link Service**: Generación de links de pago
- **Followup Service**: Programación de seguimientos
- **Notification Service**: Alertas de escalación
- **Traceability Service**: Registro de cambios

## 📊 Logs y métricas
- **State transitions**: Registro de cambios de estado con contexto
- **Transition validation**: Métricas de validaciones exitosas/fallidas
- **Timeout events**: Estados que expiran por timeout
- **Rollback events**: Rollbacks automáticos y manuales
- **Action execution**: Logs de acciones ejecutadas en transiciones
- **Performance metrics**: Tiempo de procesamiento de transiciones

## 🧪 Tests y validaciones
- ✅ **Tests de transiciones**: Verificación de cambios válidos e inválidos
- ✅ **Tests de condiciones**: Evaluación de condiciones de transición
- ✅ **Tests de timeouts**: Verificación de rollback automático
- ✅ **Tests de acciones**: Ejecución correcta de acciones
- ✅ **Tests de historial**: Registro completo de cambios
- ⚠️ **Pendiente**: Tests de concurrencia
- ⚠️ **Pendiente**: Tests de performance con alta carga

## 📋 Uso en el proyecto

### Verificación de transición
```python
from services.state_machine_service import state_machine_service, DebtorState

# Verificar si una transición es válida
context = {
    "identity_confirmed": True,
    "payment_intent": True,
    "response_sentiment": "positive"
}

can_transition = state_machine_service.can_transition(
    from_state=DebtorState.GRIS,
    to_state=DebtorState.VERDE,
    context=context
)

if can_transition:
    # Realizar transición
    pass
```

### Realizar transición de estado
```python
# Realizar transición con contexto
success = state_machine_service.transition_state(
    db=db_session,
    debtor_id=123,
    new_state=DebtorState.VERDE,
    trigger="payment_intent",
    context={
        "identity_confirmed": True,
        "payment_intent": True,
        "response_sentiment": "positive"
    },
    user_id=456,
    notes="Deudor mostró intención de pago"
)

if success:
    print("Transición exitosa")
else:
    print("Error en transición")
```

### Verificar estados temporales
```python
# Verificar si un estado es temporal
is_temporary = state_machine_service.is_temporary_state(DebtorState.PENDIENTE_PAGO)

# Obtener timeout de estado
timeout = state_machine_service.get_state_timeout(DebtorState.PENDIENTE_PAGO)
# timeout = 2880 (48 horas en minutos)
```

### Obtener transiciones válidas
```python
# Obtener todas las transiciones válidas desde un estado
valid_transitions = state_machine_service.get_valid_transitions(DebtorState.GRIS)

# Resultado: [DebtorState.VERDE, DebtorState.AMARILLO, DebtorState.ROJO]
```

## 🔧 Configuración

### Estados y transiciones
```python
# Estados base
BASE_STATES = {
    'VERDE': 'Deudor con intención de pago',
    'AMARILLO': 'Deudor en negociación',
    'ROJO': 'Deudor reacio al pago',
    'GRIS': 'Estado inicial sin clasificar'
}

# Estados temporales con timeouts
TEMPORARY_STATES = {
    'PENDIENTE_PAGO': 2880,      # 48 horas
    'EN_NEGOCIACION': 720,       # 12 horas
    'ESCALADO_HUMANO': 1440,     # 24 horas
    'EN_SEGUIMIENTO': 1440       # 24 horas
}

# Estados compuestos
COMPOSITE_STATES = {
    'VERDE_CON_DESCUENTO': 'VERDE con descuento aplicado',
    'AMARILLO_NEGOCIANDO': 'AMARILLO en proceso de negociación',
    'ROJO_ESCALADO': 'ROJO escalado a humano'
}
```

### Condiciones de transición
```python
TRANSITION_CONDITIONS = {
    'has_identity_confirmation': 'DNI validado',
    'positive_response': 'Respuesta positiva del deudor',
    'asks_for_discount': 'Deudor solicita descuento',
    'refuses_payment': 'Deudor rechaza pago',
    'aggressive_behavior': 'Comportamiento agresivo',
    'payment_intent': 'Intención clara de pago',
    'discount_accepted': 'Descuento aceptado',
    'payment_link_generated': 'Link de pago generado',
    'discount_requested': 'Descuento solicitado',
    'payment_plan_discussed': 'Plan de pago discutido',
    'counter_offer_made': 'Contraoferta realizada',
    'escalation_required': 'Escalación requerida',
    'payment_expired': 'Pago expirado',
    'negotiation_expired': 'Negociación expirada'
}
```

## 📈 Monitoreo recomendado

### Alertas críticas
- Transiciones inválidas detectadas
- Estados temporales que no expiran correctamente
- Rollbacks automáticos frecuentes
- Errores en ejecución de acciones
- Estados corruptos o inconsistentes

### Métricas importantes
- **Transition success rate**: % de transiciones exitosas
- **State distribution**: Distribución de deudores por estado
- **Timeout frequency**: Frecuencia de timeouts por estado
- **Action execution time**: Tiempo de ejecución de acciones
- **Rollback rate**: % de transiciones que requieren rollback

## 🚀 Próximas mejoras
1. **Estados anidados**: Estados con sub-estados
2. **Transiciones condicionales**: Lógica compleja de transición
3. **Estados paralelos**: Múltiples estados simultáneos
4. **Machine learning**: Predicción de próximos estados
5. **Visualización**: Dashboard de estados y transiciones
6. **Optimización**: Cache de transiciones frecuentes

## 🔒 Seguridad avanzada

### Validación de transiciones
```python
def validate_transition(from_state: str, to_state: str, context: dict) -> bool:
    """Valida si una transición es permitida"""
    # Verificar que la transición existe
    if (from_state, to_state) not in VALID_TRANSITIONS:
        return False
    
    # Verificar condiciones
    transition = VALID_TRANSITIONS[(from_state, to_state)]
    for condition in transition.conditions:
        if not evaluate_condition(condition, context):
            return False
    
    return True
```

### Prevención de ataques
- **State manipulation**: Validación estricta de transiciones
- **Race conditions**: Locks en transiciones críticas
- **Data consistency**: Verificación de integridad de estados
- **Audit trail**: Registro completo de cambios
- **Rollback protection**: Prevención de rollbacks maliciosos

### Auditoría y compliance
- **State change log**: Registro de todos los cambios de estado
- **User attribution**: Quién realizó cada cambio
- **Context preservation**: Información completa del contexto
- **Compliance reporting**: Reportes para auditorías
- **Data retention**: Políticas de retención de historial

## 📊 Ejemplos de uso

### Flujo típico de cobranza
```python
# 1. Deudor en estado GRIS
debtor.state = "GRIS"

# 2. Validar identidad y mostrar intención de pago
context = {
    "identity_confirmed": True,
    "payment_intent": True,
    "response_sentiment": "positive"
}

# 3. Transición a VERDE
state_machine_service.transition_state(
    db=db,
    debtor_id=debtor.id,
    new_state=DebtorState.VERDE,
    trigger="payment_intent",
    context=context
)

# 4. Generar link de pago (acción automática)
# 5. Transición a PENDIENTE_PAGO
# 6. Si expira, rollback a VERDE
```

### Manejo de negociación
```python
# Deudor en AMARILLO solicita descuento
context = {
    "identity_confirmed": True,
    "asks_for_discount": True,
    "discount_requested": True
}

# Transición a AMARILLO_NEGOCIANDO
state_machine_service.transition_state(
    db=db,
    debtor_id=debtor.id,
    new_state=DebtorState.AMARILLO_NEGOCIANDO,
    trigger="negotiation_active",
    context=context
)

# Acciones automáticas:
# - Ofrecer plan de pago
# - Programar seguimiento de negociación
``` 