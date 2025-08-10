from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session
from models.Debtor import Debtor
from models.DebtPayment import DebtPayment
from datetime import datetime, timedelta
import requests
import json

class PaymentLinkService:
    """Servicio para manejar la generación de links de pago según reglas de cobranza"""
    
    def __init__(self):
        # Palabras clave para detectar solicitud de link de pago (más específicas)
        self.payment_link_keywords = [
            "link de pago",
            "link para pagar", 
            "enlace de pago",
            "enlace para pagar",
            "dame el link",
            "envíame el link",
            "mandame el link",
            "dame el enlace",
            "envíame el enlace",
            "mandame el enlace",
            "quiero pagar ahora",
            "cómo pago online",
            "donde pago online",
            "pago online",
            "pago por internet",
            "transferencia",
            "débito",
            "crédito",
            "tarjeta",
            "mercadopago",
            "paypal",
            "stripe",
            "link de pago",
            "enlace de pago"
        ]
        
        # Palabras clave para detectar validación de identidad
        self.identity_validation_keywords = [
            "dni",
            "documento",
            "identidad",
            "validar",
            "confirmar",
            "verificar",
            "datos",
            "información personal",
            "email",
            "correo",
            "teléfono",
            "celular"
        ]
    
    def should_generate_payment_link(
        self, 
        user_message: str, 
        debtor_state: str, 
        conversation_history: List[Dict[str, str]],
        debtor_data: Dict[str, Any]
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Determina si se debe generar un link de pago según las reglas.
        
        Args:
            user_message: Mensaje actual del usuario
            debtor_state: Estado actual del deudor (VERDE, AMARILLO, ROJO, GRIS)
            conversation_history: Historial de conversación
            debtor_data: Datos del deudor
            
        Returns:
            Tuple con (debe_generar, razón, datos_adicionales)
        """
        normalized_message = user_message.lower().strip()
        
        # 1. Verificar si el deudor validó su identidad
        identity_validated = self._check_identity_validation(conversation_history, debtor_data)
        
        if not identity_validated:
            return False, "IDENTITY_NOT_VALIDATED", {
                "message": "El deudor no ha validado su identidad aún",
                "required_fields": self._get_required_identity_fields(debtor_data)
            }
        
        # 2. Verificar si el mensaje solicita un link de pago
        requests_payment_link = self._detect_payment_link_request(normalized_message)
        
        if not requests_payment_link:
            return False, "NO_PAYMENT_LINK_REQUESTED", {
                "message": "El deudor no solicitó explícitamente un link de pago"
            }
        
        # 3. Aplicar reglas según el estado
        if debtor_state == "VERDE":
            return True, "VERDE_STATE_IMMEDIATE", {
                "message": "Deudor en estado VERDE solicita link de pago",
                "response_template": "Claro, puedo generarte un link de pago inmediato. Tené en cuenta que vence en 48 hs.",
                "urgency": "high"
            }
        
        elif debtor_state == "AMARILLO":
            return True, "AMARILLO_STATE_EXPLICIT_REQUEST", {
                "message": "Deudor en estado AMARILLO solicita explícitamente link de pago",
                "response_template": "¿Querés que te envíe el link para pagar?",
                "urgency": "medium"
            }
        
        elif debtor_state == "ROJO":
            return False, "ROJO_STATE_NO_AUTO_GENERATION", {
                "message": "Deudor en estado ROJO - no generar link automáticamente",
                "response_template": "Entiendo tu situación. Un especialista se pondrá en contacto contigo para ayudarte.",
                "requires_human_intervention": True
            }
        
        elif debtor_state == "GRIS":
            return False, "GRIS_STATE_NO_AUTO_GENERATION", {
                "message": "Deudor en estado GRIS - no generar link automáticamente",
                "response_template": "Gracias por tu interés. Un especialista se pondrá en contacto contigo.",
                "requires_human_intervention": True
            }
        
        return False, "UNKNOWN_STATE", {"message": "Estado desconocido"}
    
    def generate_payment_link_response(
        self, 
        debtor_state: str, 
        debtor_data: Dict[str, Any],
        decision_data: Dict[str, Any]
    ) -> str:
        """
        Genera la respuesta apropiada para el link de pago según el estado.
        
        Args:
            debtor_state: Estado del deudor
            debtor_data: Datos del deudor
            decision_data: Datos de la decisión tomada
            
        Returns:
            Respuesta formateada para el deudor
        """
        debt_amount = debtor_data.get("deuda", 0)
        
        if debtor_state == "VERDE":
            return f"""Perfecto, te comparto el link para regularizar tu deuda de manera segura y rápida.

📋 Información del pago:
• Monto a pagar: ${debt_amount:,.2f}
• Vencimiento del link: 48 horas
• Método de pago: Online (tarjeta, transferencia, etc.)

🔗 Link de pago: [GENERAR_LINK_AQUI]

⚠️ Importante: El link vence en 48 horas por seguridad. Si tenés alguna consulta sobre el pago, no dudes en preguntarme."""
        
        elif debtor_state == "AMARILLO":
            return f"""Entiendo tu situación. ¿Querés que te envíe el link con el descuento vigente?

Tu deuda es de ${debt_amount:,.2f} y tenemos opciones de descuento disponibles.

¿Querés que te lo envíe ahora mismo por este medio?"""
        
        else:
            return decision_data.get("response_template", "Gracias por tu interés. Un especialista se pondrá en contacto contigo.")
    
    def _check_identity_validation(
        self, 
        conversation_history: List[Dict[str, str]], 
        debtor_data: Dict[str, Any]
    ) -> bool:
        """
        Verifica si el deudor ha validado su identidad.
        
        Args:
            conversation_history: Historial de conversación
            debtor_data: Datos del deudor
            
        Returns:
            True si la identidad está validada
        """
        # Verificar si tenemos datos básicos de identidad en debtor_data
        required_fields = self._get_required_identity_fields(debtor_data)
        
        # Verificar que al menos un campo de identidad esté presente en debtor_data
        for field in required_fields:
            if debtor_data.get(field):
                return True
        
        # Si no encontramos identidad en debtor_data, verificar en el historial
        return self._check_identity_in_conversation(conversation_history)
    
    def _get_required_identity_fields(self, debtor_data: Dict[str, Any]) -> List[str]:
        """
        Obtiene los campos de identidad requeridos según los datos disponibles.
        
        Args:
            debtor_data: Datos del deudor
            
        Returns:
            Lista de campos requeridos
        """
        # Campos que podrían estar disponibles
        possible_fields = ["dni", "email", "nombre", "apellido", "documento"]
        
        # Verificar cuáles están disponibles en los datos
        available_fields = [field for field in possible_fields if field in debtor_data]
        
        # Si no hay campos específicos, usar campos genéricos
        if not available_fields:
            return ["identidad_validada", "datos_confirmados"]
        
        return available_fields
    
    def _check_identity_in_conversation(self, conversation_history: List[Dict[str, str]]) -> bool:
        """
        Verifica si la identidad fue validada en la conversación.
        
        Args:
            conversation_history: Historial de conversación
            
        Returns:
            True si se detecta validación de identidad
        """
        identity_keywords = [
            "dni", "documento", "identidad", "validar", "confirmar", 
            "email", "correo", "datos", "información"
        ]
        
        for message in conversation_history:
            if message.get("role") == "user":
                content = message.get("content", "").lower().strip()
                
                # Detectar palabras clave de identidad
                if any(keyword in content for keyword in identity_keywords):
                    return True
                
                # Detectar números de DNI (7+ dígitos)
                if content.isdigit() and len(content) >= 7:
                    return True
                
                # Detectar frases que contengan DNI
                if "dni" in content or "documento" in content:
                    return True
        
        return False
    
    def _detect_payment_link_request(self, normalized_message: str) -> bool:
        """
        Detecta si el mensaje solicita un link de pago de manera específica.
        
        Args:
            normalized_message: Mensaje normalizado en minúsculas
            
        Returns:
            True si solicita link de pago de manera específica
        """
        # Palabras que indican una solicitud específica de link/enlace
        specific_request_keywords = [
            "dame el link",
            "envíame el link", 
            "mandame el link",
            "dame el enlace",
            "envíame el enlace",
            "mandame el enlace",
            "link de pago",
            "enlace de pago",
            "link para pagar",
            "enlace para pagar",
            "quiero pagar ahora",
            "cómo pago online",
            "donde pago online",
            "pasar el link",
            "pasar el enlace",
            "dame el link de pago",
            "envíame el link de pago",
            "mandame el link de pago"
        ]
        
        # Palabras que indican intención de pago (más flexibles)
        payment_intent_keywords = [
            "quiero pagar",
            "pagar ahora",
            "pago ahora",
            "pagar online",
            "pago online",
            "pagar por internet",
            "pago por internet",
            "pagar con tarjeta",
            "pago con tarjeta",
            "pagar con débito",
            "pago con débito",
            "pagar con crédito",
            "pago con crédito"
        ]
        
        # Palabras que indican métodos de pago específicos (solo en contexto de solicitud)
        payment_method_keywords = [
            "pago online",
            "pago por internet", 
            "transferencia",
            "débito",
            "crédito",
            "mercadopago",
            "paypal",
            "stripe"
        ]
        
        # Verificar solicitudes específicas
        if any(keyword in normalized_message for keyword in specific_request_keywords):
            return True
        
        # Verificar intención de pago (más flexible)
        if any(keyword in normalized_message for keyword in payment_intent_keywords):
            return True
            
        # Verificar métodos de pago específicos (solo si están en contexto de solicitud)
        if any(keyword in normalized_message for keyword in payment_method_keywords):
            # Verificar que no sea solo una pregunta general
            general_questions = ["qué", "que", "como", "cómo", "donde", "dónde", "cuando", "cuándo", "puedo", "se puede"]
            if not any(question in normalized_message for question in general_questions):
                return True
                
        return False
    
    def create_payment_link(
        self, 
        debtor_id: int, 
        amount: float, 
        discount: Optional[float] = None,
        method: str = "mock"
    ) -> Dict[str, Any]:
        """
        Crea un link de pago real o simulado.
        
        Args:
            debtor_id: ID del deudor
            amount: Monto a pagar
            discount: Descuento aplicado (opcional)
            method: Método de pago
            
        Returns:
            Diccionario con información del link de pago
        """
        # Calcular monto final con descuento
        final_amount = amount
        if discount:
            final_amount = amount * (1 - discount / 100)
        
        # Generar link de pago (mock por ahora)
        payment_link = f"https://mockpay.com/pay/{debtor_id}/{int(datetime.utcnow().timestamp())}"
        external_reference = f"mock-{debtor_id}-{int(datetime.utcnow().timestamp())}"
        expires_at = datetime.utcnow() + timedelta(hours=48)
        
        return {
            "payment_link": payment_link,
            "external_reference": external_reference,
            "amount_requested": amount,
            "final_amount": final_amount,
            "discount_applied": discount,
            "expires_at": expires_at,
            "method": method,
            "status": "pending"
        }

# Instancia global del servicio
payment_link_service = PaymentLinkService() 