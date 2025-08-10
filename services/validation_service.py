import re
import html
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class ValidationSeverity(Enum):
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class ValidationResult:
    """Resultado de una validación"""
    is_valid: bool
    message: str
    severity: ValidationSeverity = ValidationSeverity.ERROR
    sanitized_value: Optional[str] = None

class ValidationService:
    """Servicio centralizado para validación y sanitización de datos"""
    
    def __init__(self):
        # Patrones de validación
        self.patterns = {
            'dni': r'^\d{7,8}$',
            'phone': r'^\+?54?\d{10,11}$',
            'email': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
            'amount': r'^\d+(\.\d{1,2})?$',
            'date': r'^\d{4}-\d{2}-\d{2}$'
        }
        
        # Palabras prohibidas para prevenir inyección de prompts
        self.forbidden_prompt_keywords = [
            'system:', 'user:', 'assistant:', 'role:', 'content:',
            'ignore previous', 'ignore above', 'new instructions',
            'act as', 'pretend to be', 'you are now',
            'bypass', 'override', 'ignore rules',
            '<script>', '</script>', 'javascript:',
            'data:text/html', 'vbscript:', 'onload=',
            'onerror=', 'onclick=', 'onmouseover='
        ]
        
        # Caracteres peligrosos para sanitización
        self.dangerous_chars = ['<', '>', '"', "'", '&', '{', '}', '[', ']', '|', '\\', '/']
    
    def validate_dni(self, dni: str) -> ValidationResult:
        """Valida formato de DNI argentino"""
        if not dni:
            return ValidationResult(False, "DNI no puede estar vacío")
        
        # Limpiar espacios y guiones
        clean_dni = re.sub(r'[\s\-\.]', '', dni)
        
        if not re.match(self.patterns['dni'], clean_dni):
            return ValidationResult(False, "DNI debe tener 7 u 8 dígitos numéricos")
        
        # Validar que no sea todo ceros
        if clean_dni == '0' * len(clean_dni):
            return ValidationResult(False, "DNI no puede ser todo ceros")
        
        return ValidationResult(True, "DNI válido", ValidationSeverity.WARNING, clean_dni)
    
    def validate_phone(self, phone: str) -> ValidationResult:
        """Valida formato de teléfono argentino"""
        if not phone:
            return ValidationResult(False, "Teléfono no puede estar vacío")
        
        # Limpiar espacios, guiones y paréntesis
        clean_phone = re.sub(r'[\s\-\(\)]', '', phone)
        
        # Agregar código de país si no está presente
        if clean_phone.startswith('0'):
            clean_phone = '54' + clean_phone[1:]
        elif not clean_phone.startswith('+') and not clean_phone.startswith('54'):
            clean_phone = '54' + clean_phone
        
        if not re.match(self.patterns['phone'], clean_phone):
            return ValidationResult(False, "Formato de teléfono inválido. Debe ser: +54XXXXXXXXXX")
        
        return ValidationResult(True, "Teléfono válido", ValidationSeverity.WARNING, clean_phone)
    
    def validate_email(self, email: str) -> ValidationResult:
        """Valida formato de email"""
        if not email:
            return ValidationResult(False, "Email no puede estar vacío")
        
        clean_email = email.strip().lower()
        
        if not re.match(self.patterns['email'], clean_email):
            return ValidationResult(False, "Formato de email inválido")
        
        return ValidationResult(True, "Email válido", ValidationSeverity.WARNING, clean_email)
    
    def validate_amount(self, amount: Union[str, float, int]) -> ValidationResult:
        """Valida formato de monto"""
        if amount is None:
            return ValidationResult(False, "Monto no puede estar vacío")
        
        amount_str = str(amount).strip()
        
        if not re.match(self.patterns['amount'], amount_str):
            return ValidationResult(False, "Formato de monto inválido. Debe ser un número positivo")
        
        try:
            amount_float = float(amount_str)
            if amount_float <= 0:
                return ValidationResult(False, "Monto debe ser mayor a 0")
        except ValueError:
            return ValidationResult(False, "Monto debe ser un número válido")
        
        return ValidationResult(True, "Monto válido", ValidationSeverity.WARNING, amount_str)
    
    def sanitize_input(self, text: str, max_length: int = 1000) -> ValidationResult:
        """Sanitiza entrada de texto para prevenir inyección de prompts y XSS"""
        if not text:
            return ValidationResult(True, "Texto vacío", ValidationSeverity.WARNING, "")
        
        # Verificar longitud
        if len(text) > max_length:
            return ValidationResult(False, f"Texto demasiado largo. Máximo {max_length} caracteres")
        
        # Convertir a string y limpiar
        clean_text = str(text).strip()
        
        # Verificar palabras prohibidas (insensible a mayúsculas/minúsculas)
        text_lower = clean_text.lower()
        for keyword in self.forbidden_prompt_keywords:
            if keyword.lower() in text_lower:
                return ValidationResult(
                    False, 
                    f"Texto contiene palabras prohibidas: {keyword}",
                    ValidationSeverity.CRITICAL
                )
        
        # Escapar caracteres HTML
        sanitized = html.escape(clean_text)
        
        # Verificar caracteres peligrosos
        dangerous_found = [char for char in self.dangerous_chars if char in clean_text]
        if dangerous_found:
            logger.warning(f"Caracteres peligrosos detectados: {dangerous_found}")
            # No rechazar, solo loggear y sanitizar
        
        return ValidationResult(True, "Texto sanitizado", ValidationSeverity.WARNING, sanitized)
    
    def validate_custom_field(self, field_name: str, value: Any, field_type: str = "text") -> ValidationResult:
        """Valida campos personalizados según su tipo"""
        if not field_name:
            return ValidationResult(False, "Nombre de campo no puede estar vacío")
        
        # Sanitizar nombre del campo
        field_validation = self.sanitize_input(field_name, max_length=50)
        if not field_validation.is_valid:
            return field_validation
        
        # Validar según tipo
        if field_type == "dni":
            return self.validate_dni(str(value))
        elif field_type == "phone":
            return self.validate_phone(str(value))
        elif field_type == "email":
            return self.validate_email(str(value))
        elif field_type == "amount":
            return self.validate_amount(value)
        elif field_type == "date":
            return self._validate_date(str(value))
        else:  # text
            return self.sanitize_input(str(value))
    
    def _validate_date(self, date_str: str) -> ValidationResult:
        """Valida formato de fecha YYYY-MM-DD"""
        if not date_str:
            return ValidationResult(False, "Fecha no puede estar vacía")
        
        if not re.match(self.patterns['date'], date_str):
            return ValidationResult(False, "Formato de fecha inválido. Debe ser YYYY-MM-DD")
        
        try:
            from datetime import datetime
            datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            return ValidationResult(False, "Fecha inválida")
        
        return ValidationResult(True, "Fecha válida", ValidationSeverity.WARNING, date_str)
    
    def validate_debtor_data(self, debtor_data: Dict[str, Any]) -> List[ValidationResult]:
        """Valida todos los datos de un deudor"""
        results = []
        
        # Validar campos obligatorios
        if 'dni' in debtor_data:
            results.append(self.validate_dni(str(debtor_data['dni'])))
        
        if 'phone' in debtor_data:
            results.append(self.validate_phone(str(debtor_data['phone'])))
        
        if 'email' in debtor_data:
            results.append(self.validate_email(str(debtor_data['email'])))
        
        if 'deuda' in debtor_data:
            results.append(self.validate_amount(debtor_data['deuda']))
        
        # Validar campos personalizados
        if 'custom_data' in debtor_data and isinstance(debtor_data['custom_data'], dict):
            for field_name, field_value in debtor_data['custom_data'].items():
                # Intentar detectar tipo automáticamente
                field_type = self._detect_field_type(field_name, field_value)
                results.append(self.validate_custom_field(field_name, field_value, field_type))
        
        return results
    
    def _detect_field_type(self, field_name: str, value: Any) -> str:
        """Detecta automáticamente el tipo de campo basado en nombre y valor"""
        field_lower = field_name.lower()
        value_str = str(value).lower()
        
        if any(keyword in field_lower for keyword in ['dni', 'documento', 'cedula']):
            return 'dni'
        elif any(keyword in field_lower for keyword in ['phone', 'telefono', 'celular', 'movil']):
            return 'phone'
        elif any(keyword in field_lower for keyword in ['email', 'correo', 'mail']):
            return 'email'
        elif any(keyword in field_lower for keyword in ['amount', 'monto', 'deuda', 'saldo', 'precio']):
            return 'amount'
        elif any(keyword in field_lower for keyword in ['date', 'fecha', 'nacimiento']):
            return 'date'
        else:
            return 'text'
    
    def get_validation_summary(self, results: List[ValidationResult]) -> Dict[str, Any]:
        """Genera un resumen de validaciones"""
        total = len(results)
        valid = sum(1 for r in results if r.is_valid)
        errors = [r for r in results if not r.is_valid and r.severity == ValidationSeverity.ERROR]
        critical = [r for r in results if r.severity == ValidationSeverity.CRITICAL]
        warnings = [r for r in results if r.severity == ValidationSeverity.WARNING]
        
        return {
            'total_validations': total,
            'valid_count': valid,
            'error_count': len(errors),
            'critical_count': len(critical),
            'warning_count': len(warnings),
            'is_valid': len(errors) == 0 and len(critical) == 0,
            'errors': [{'message': r.message, 'severity': r.severity.value} for r in errors],
            'critical_errors': [{'message': r.message, 'severity': r.severity.value} for r in critical],
            'warnings': [{'message': r.message, 'severity': r.severity.value} for r in warnings]
        }

# Instancia global del servicio
validation_service = ValidationService() 