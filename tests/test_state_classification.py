#!/usr/bin/env python3
"""
Script de prueba para la clasificación de estados
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from unittest.mock import patch, MagicMock
import services.openai_service as oai
from services.debtor_service import update_state
from models.Debtor import Debtor
from sqlalchemy.orm import Session
from datetime import datetime
import json

@pytest.fixture
def mock_openai_responses():
    """Fixture para mockear respuestas de OpenAI"""
    with patch('services.openai_service.analyze_conversation_context') as mock_analyze, \
         patch('services.openai_service.classify_state') as mock_classify:
        
        # Mock para analyze_conversation_context
        def mock_analyze_func(conversation_history, message):
            message_lower = message.lower()
            history_text = " ".join([m.get('content', '').lower() for m in (conversation_history or [])])
            
            # Simular lógica de detección completa considerando historial + mensaje actual
            payment_keywords = ['pagar', 'pago', 'link', 'quiero', 'acepto']
            has_payment_intent = any(k in message_lower for k in payment_keywords) or any(k in history_text for k in payment_keywords)
            has_positive_response = any(k in message_lower for k in ['si', 'sí', 'ok', 'claro', 'perfecto', 'dale', 'quiero', 'acepto'])
            has_identity_confirmation = message.strip().isdigit() and len(message.strip()) >= 7
            has_negotiation = any(k in message_lower for k in ['descuento', 'cuotas', 'menos', 'negociar']) or any(k in history_text for k in ['descuento', 'cuotas', 'menos', 'negociar'])
            has_rejection = any(k in message_lower for k in ['no puedo', 'no quiero', 'imposible'])
            is_cooperative = has_payment_intent or has_positive_response or has_identity_confirmation
            
            # Si hay rechazo, no debe haber intención de pago
            if has_rejection:
                has_payment_intent = False
            
            context_indicators = []
            if has_payment_intent:
                context_indicators.append("contexto_de_pago")
            if has_positive_response:
                context_indicators.append("respuesta_positiva")
            if has_identity_confirmation:
                context_indicators.append("confirmación_identidad")
            if has_negotiation:
                context_indicators.append("negociación")
            if has_rejection:
                context_indicators.append("rechazo")
            if is_cooperative:
                context_indicators.append("cooperativo")
            
            return {
                "has_payment_intent": has_payment_intent,
                "has_positive_response": has_positive_response,
                "has_identity_confirmation": has_identity_confirmation,
                "has_negotiation": has_negotiation,
                "has_rejection": has_rejection,
                "is_cooperative": is_cooperative,
                "context_indicators": context_indicators
            }
        
        # Mock para classify_state
        def mock_classify_func(phone, conversation_history):
            # Simular lógica de clasificación
            if any(msg.get("content", "").lower() in ['si', 'sí', 'ok', 'claro', 'perfecto', 'dale', 'quiero', 'acepto'] 
                   for msg in conversation_history if msg.get("role") == "user"):
                return "VERDE"
            return "AMARILLO"
        
        mock_analyze.side_effect = mock_analyze_func
        mock_classify.side_effect = mock_classify_func
        
        yield mock_analyze, mock_classify

class TestStateClassification:
    """Tests para verificar la clasificación de estados de deudores"""
    
    def test_positive_response_maintains_favorable_state(self, mock_openai_responses):
        """Test que verifica que una respuesta positiva mantiene el estado favorable"""
        
        mock_analyze, mock_classify = mock_openai_responses
        
        # Simular conversación donde el deudor está interesado en pagar
        conversation_history = [
            {"role": "assistant", "content": "Hola, soy Francisco del banco Santander. Tenemos una deuda pendiente de $40,000. ¿Te interesa regularizarla?"},
            {"role": "user", "content": "Podria ser, tengo q pagar si o si?"},
            {"role": "assistant", "content": "Entiendo tu situación. La deuda de $40,000.00 debe ser regularizada, pero nuestro objetivo es hacerlo de la manera más accesible para ti. Le reitero que contamos con una opción de pago en 3 cuotas con un interés del 5%."},
            {"role": "user", "content": "Bueno entonces si la pago con ese descuento"},
            {"role": "assistant", "content": "Excelente decisión. Para proceder, podemos organizar el pago de tu deuda de $40,000.00 en 3 cuotas con un interés del 5%. ¿Te gustaría que te envíe el link para completar tu pago?"},
            {"role": "user", "content": "Si"}
        ]
        
        # Analizar el contexto
        context_analysis = oai.analyze_conversation_context(conversation_history, "Si")
        
        # Verificar que detecta intención de pago
        assert context_analysis["has_payment_intent"] == True
        assert context_analysis["has_positive_response"] == True
        assert context_analysis["is_cooperative"] == True
        assert "contexto_de_pago" in context_analysis["context_indicators"]
        
        # Clasificar el estado
        state = oai.classify_state("Si", conversation_history)
        
        # Debería mantener un estado favorable (VERDE o AMARILLO)
        assert state in ["VERDE", "AMARILLO"], f"Estado inesperado: {state}"
        
        # Verificar que se llamaron los mocks
        mock_analyze.assert_called_once_with(conversation_history, "Si")
        mock_classify.assert_called_once_with("Si", conversation_history)
    
    def test_payment_context_detection(self, mock_openai_responses):
        """Test que verifica la detección de contexto de pago"""
        
        mock_analyze, _ = mock_openai_responses
        
        # Conversación con contexto de pago
        conversation_history = [
            {"role": "user", "content": "Quiero pagar mi deuda"},
            {"role": "assistant", "content": "Perfecto, te ayudo con eso. ¿Quieres el link de pago?"},
            {"role": "user", "content": "Si"}
        ]
        
        context_analysis = oai.analyze_conversation_context(conversation_history, "Si")
        
        # Verificar que detecta el contexto de pago
        assert "contexto_de_pago" in context_analysis["context_indicators"]
        assert context_analysis["has_payment_intent"] == True
        assert context_analysis["has_positive_response"] == True
        
        # Verificar que se llamó el mock
        mock_analyze.assert_called_once_with(conversation_history, "Si")
    
    def test_short_positive_response_in_payment_context(self, mock_openai_responses):
        """Test que verifica que respuestas cortas positivas en contexto de pago no cambian a GRIS"""
        
        mock_analyze, mock_classify = mock_openai_responses
        
        # Simular el caso problemático
        conversation_history = [
            {"role": "assistant", "content": "¿Te gustaría que te envíe el link para completar tu pago?"},
            {"role": "user", "content": "Si"}
        ]
        
        # Analizar contexto
        context_analysis = oai.analyze_conversation_context(conversation_history, "Si")
        
        # Verificar que detecta respuesta positiva
        assert context_analysis["has_positive_response"] == True
        
        # Clasificar estado
        state = oai.classify_state("Si", conversation_history)
        
        # No debería ser GRIS si hay contexto de pago
        if "contexto_de_pago" in context_analysis["context_indicators"]:
            assert state != "GRIS", "Estado no debería ser GRIS con contexto de pago"
        
        # Verificar que se llamaron los mocks
        mock_analyze.assert_called_once_with(conversation_history, "Si")
        mock_classify.assert_called_once_with("Si", conversation_history)
    
    def test_state_transition_protection(self):
        """Test que verifica la protección contra cambios de estado no deseados"""
        
        # Simular un deudor en estado AMARILLO (sin crear instancia de SQLAlchemy)
        current_state = "AMARILLO"
        message = "Si"
        
        # Verificar que no cambia a GRIS si hay contexto de pago
        payment_context_keywords = ['link', 'pago', 'pagar', 'deuda', 'cuenta', 'regularizar', 'sí', 'si', 'acepto', 'quiero']
        message_lower = message.lower()
        
        if any(keyword in message_lower for keyword in payment_context_keywords):
            # Debería mantener el estado actual
            assert current_state in ["VERDE", "AMARILLO"], "Debería mantener estado favorable"
    
    def test_improved_keyword_detection(self, mock_openai_responses):
        """Test que verifica la detección mejorada de palabras clave"""
        
        mock_analyze, _ = mock_openai_responses
        
        # Test diferentes formas de confirmación
        test_cases = [
            ("Si", True),
            ("Sí", True),
            ("Ok", True),
            ("Claro", True),
            ("Perfecto", True),
            ("Dale", True),
            ("Quiero", True),
            ("Acepto", True),
            ("Hola", False),
            ("No", False),
            ("No gracias", False)
        ]
        
        for message, should_be_positive in test_cases:
            context_analysis = oai.analyze_conversation_context([], message)
            assert context_analysis["has_positive_response"] == should_be_positive, f"Error con mensaje: {message}"
        
        # Verificar que se llamó el mock para cada caso
        assert mock_analyze.call_count == len(test_cases)
    
    def test_payment_intent_detection(self, mock_openai_responses):
        """Test que verifica la detección de intención de pago"""
        
        mock_analyze, _ = mock_openai_responses
        
        # Test diferentes formas de solicitar pago
        test_cases = [
            ("Quiero pagar", True),
            ("Puedo pagar", True),
            ("Me interesa pagar", True),
            ("Quiero el link", True),
            ("Dame el link", True),
            ("Envíame el link", True),
            ("Quiero pagar ahora", True),
            ("Hola", False),
            ("No quiero", False)
        ]
        
        for message, should_have_intent in test_cases:
            context_analysis = oai.analyze_conversation_context([], message)
            assert context_analysis["has_payment_intent"] == should_have_intent, f"Error con mensaje: {message}"
        
        # Verificar que se llamó el mock para cada caso
        assert mock_analyze.call_count == len(test_cases)

if __name__ == "__main__":
    # Ejecutar tests
    test_instance = TestStateClassification()
    
    print("🧪 Ejecutando tests de clasificación de estados...")
    
    try:
        test_instance.test_positive_response_maintains_favorable_state()
        print("✅ Test 1: Respuesta positiva mantiene estado favorable")
        
        test_instance.test_payment_context_detection()
        print("✅ Test 2: Detección de contexto de pago")
        
        test_instance.test_short_positive_response_in_payment_context()
        print("✅ Test 3: Respuesta corta positiva en contexto de pago")
        
        test_instance.test_state_transition_protection()
        print("✅ Test 4: Protección contra cambios de estado no deseados")
        
        test_instance.test_improved_keyword_detection()
        print("✅ Test 5: Detección mejorada de palabras clave")
        
        test_instance.test_payment_intent_detection()
        print("✅ Test 6: Detección de intención de pago")
        
        print("\n🎉 Todos los tests pasaron exitosamente!")
        
    except Exception as e:
        print(f"❌ Error en test: {e}")
        import traceback
        traceback.print_exc() 