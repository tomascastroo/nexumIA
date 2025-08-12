# Validation Service

## 🧠 Descripción general
Servicio de validación y sanitización de datos de entrada. Previene inyecciones, valida formatos específicos para Argentina y asegura integridad de datos antes de procesamiento. Es fundamental para la seguridad del sistema.

## ⚙️ Funcionalidades principales
- **Validación de DNI**: Formato argentino (7-8 dígitos numéricos)
- **Validación de teléfonos**: Formato argentino con código de país (+54)
- **Validación de emails**: Formato estándar con validación de dominio
- **Validación de montos**: Números positivos con hasta 2 decimales
- **Sanitización de texto**: Prevención de XSS e inyección de prompts
- **Validación de campos personalizados**: Detección automática de tipos
- **Validación de fechas**: Formato YYYY-MM-DD

## 🔐 Consideraciones de seguridad
- **Prevención XSS**: Escape de caracteres peligrosos (`<`, `>`, `"`, `'`, `&`)
- **Inyección de prompts**: Detección de palabras prohibidas (`system:`, `ignore previous`, etc.)
- **Sanitización**: Limpieza de entrada antes de procesamiento
- **Validación estricta**: Rechazo de datos malformados
- **Límites de longitud**: Prevención de ataques de buffer overflow

## ⚠️ Errores posibles y manejo
- **Datos inválidos**: Respuestas descriptivas con sugerencias de formato
- **Texto muy largo**: Truncamiento automático (máximo 1000 caracteres)
- **Caracteres peligrosos**: Logging y sanitización automática
- **Palabras prohibidas**: Rechazo inmediato con logging crítico
- **Campos vacíos**: Validación según tipo (obligatorio/opcional)

## 📡 Integraciones externas
- **Sin integraciones externas**: Servicio autónomo para validación local
- **Integración con modelos**: Validación antes de guardar en base de datos
- **Integración con APIs**: Validación de payloads de entrada

## 📊 Logs y métricas
- **Validation errors**: Errores de validación con contexto completo
- **Sanitization warnings**: Caracteres peligrosos detectados y sanitizados
- **Critical violations**: Intentos de inyección de prompts con IP y timestamp
- **Validation summary**: Estadísticas de validaciones por tipo y resultado
- **Performance metrics**: Tiempo de validación por tipo de dato

## 🧪 Tests y validaciones
- ✅ **Tests de DNI**: Formatos válidos e inválidos, con y sin espacios
- ✅ **Tests de teléfonos**: Diferentes formatos argentinos (con/sin código país)
- ✅ **Tests de sanitización**: XSS y inyección de prompts
- ✅ **Tests de montos**: Números positivos, negativos, cero y decimales
- ✅ **Tests de emails**: Formatos válidos e inválidos
- ✅ **Tests de fechas**: Formatos correctos e incorrectos
- ⚠️ **Pendiente**: Tests de performance con grandes volúmenes de datos
- ⚠️ **Pendiente**: Tests de concurrencia

## 📋 Uso en el proyecto

### Validación básica
```python
from services.validation_service import validation_service

# Validar DNI
result = validation_service.validate_dni("12345678")
if result.is_valid:
    clean_dni = result.sanitized_value
else:
    print(f"Error: {result.message}")

# Validar teléfono
result = validation_service.validate_phone("+5491112345678")
if result.is_valid:
    clean_phone = result.sanitized_value
```

### Validación de datos de deudor
```python
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

if summary['is_valid']:
    # Procesar datos válidos
    pass
else:
    # Manejar errores de validación
    for error in summary['errors']:
        print(f"Error: {error['message']}")
```

### Sanitización de entrada
```python
# Sanitizar texto de entrada
result = validation_service.sanitize_input(user_input)
if result.is_valid:
    clean_text = result.sanitized_value
else:
    # Rechazar entrada peligrosa
    raise ValueError(f"Entrada no válida: {result.message}")
```

## 🔧 Configuración

### Patrones de validación
```python
# DNI argentino
DNI_PATTERN = r'^\d{7,8}$'

# Teléfono argentino
PHONE_PATTERN = r'^\+?54?\d{10,11}$'

# Email
EMAIL_PATTERN = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

# Monto
AMOUNT_PATTERN = r'^\d+(\.\d{1,2})?$'

# Fecha
DATE_PATTERN = r'^\d{4}-\d{2}-\d{2}$'
```

### Palabras prohibidas
```python
FORBIDDEN_KEYWORDS = [
    'system:', 'user:', 'assistant:', 'role:', 'content:',
    'ignore previous', 'ignore above', 'new instructions',
    'act as', 'pretend to be', 'you are now',
    'bypass', 'override', 'ignore rules',
    '<script>', '</script>', 'javascript:',
    'data:text/html', 'vbscript:', 'onload=',
    'onerror=', 'onclick=', 'onmouseover='
]
```

### Límites de configuración
```python
# Longitudes máximas
MAX_TEXT_LENGTH = 1000
MAX_FIELD_NAME_LENGTH = 50
MAX_CUSTOM_FIELDS = 20

# Configuración de severidad
VALIDATION_SEVERITY = {
    'LOW': 'warning',
    'MEDIUM': 'error', 
    'HIGH': 'critical'
}
```

## 📈 Monitoreo recomendado

### Alertas críticas
- Intentos de inyección de prompts detectados
- Tasa de validación fallida > 10%
- Tiempo de validación promedio > 100ms
- Errores de validación en campos críticos (DNI, teléfono)

### Métricas importantes
- **Validation success rate**: % de validaciones exitosas por tipo
- **Sanitization rate**: % de textos que requieren sanitización
- **Critical violations**: Número de intentos de inyección por día
- **Performance**: Tiempo promedio de validación por tipo de dato
- **Error distribution**: Tipos de errores más comunes

## 🚀 Próximas mejoras
1. **Validación en tiempo real**: Feedback inmediato en frontend
2. **Auto-corrección**: Sugerencias automáticas para datos malformados
3. **Validación avanzada**: Verificación de DNI contra base de datos
4. **Machine learning**: Detección de patrones de fraude
5. **Validación distribuida**: Cache de validaciones frecuentes
6. **Validación asíncrona**: Para grandes volúmenes de datos

## 🔒 Seguridad avanzada

### Prevención de ataques
- **SQL Injection**: Validación estricta de tipos de datos
- **XSS**: Escape completo de caracteres peligrosos
- **Prompt Injection**: Detección de palabras clave maliciosas
- **Buffer Overflow**: Límites estrictos de longitud
- **Data Leakage**: No logging de datos sensibles

### Auditoría
- **Log de intentos de inyección**: Con IP y timestamp
- **Métricas de seguridad**: Tasa de detección de ataques
- **Alertas automáticas**: Para patrones sospechosos
- **Reportes de compliance**: Para auditorías de seguridad 