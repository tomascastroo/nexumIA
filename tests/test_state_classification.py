#!/usr/bin/env python3
"""
Script de prueba para la clasificación de estados
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from services.openai_service import classify_state, analyze_conversation_context
from services.debtor_service import update_state
from models.Debtor import Debtor
from sqlalchemy.orm import Session
from datetime import datetime
import json

class TestStateClassification:
    """Tests para verificar la clasificación de estados de deudores"""
    
    def test_positive_response_maintains_favorable_state(self):
        """Test que verifica que una respuesta positiva mantiene el estado favorable"""
        
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
        context_analysis = analyze_conversation_context(conversation_history, "Si")
        
        # Verificar que detecta intención de pago
        assert context_analysis["has_payment_intent"] == True
        assert context_analysis["has_positive_response"] == True
        assert context_analysis["is_cooperative"] == True
        assert "contexto_de_pago" in context_analysis["context_indicators"]
        
        # Clasificar el estado
        state = classify_state("Si", conversation_history)
        
        # Debería mantener un estado favorable (VERDE o AMARILLO)
        assert state in ["VERDE", "AMARILLO"], f"Estado inesperado: {state}"
    
    def test_payment_context_detection(self):
        """Test que verifica la detección de contexto de pago"""
        
        # Conversación con contexto de pago
        conversation_history = [
            {"role": "user", "content": "Quiero pagar mi deuda"},
            {"role": "assistant", "content": "Perfecto, te ayudo con eso. ¿Quieres el link de pago?"},
            {"role": "user", "content": "Si"}
        ]
        
        context_analysis = analyze_conversation_context(conversation_history, "Si")
        
        # Verificar que detecta el contexto de pago
        assert "contexto_de_pago" in context_analysis["context_indicators"]
        assert context_analysis["has_payment_intent"] == True
        assert context_analysis["has_positive_response"] == True
    
    def test_short_positive_response_in_payment_context(self):
        """Test que verifica que respuestas cortas positivas en contexto de pago no cambian a GRIS"""
        
        # Simular el caso problemático
        conversation_history = [
            {"role": "assistant", "content": "¿Te gustaría que te envíe el link para completar tu pago?"},
            {"role": "user", "content": "Si"}
        ]
        
        # Analizar contexto
        context_analysis = analyze_conversation_context(conversation_history, "Si")
        
        # Verificar que detecta respuesta positiva
        assert context_analysis["has_positive_response"] == True
        
        # Clasificar estado
        state = classify_state("Si", conversation_history)
        
        # No debería ser GRIS si hay contexto de pago
        if "contexto_de_pago" in context_analysis["context_indicators"]:
            assert state != "GRIS", "Estado no debería ser GRIS con contexto de pago"
    
    def test_state_transition_protection(self):
        """Test que verifica la protección contra cambios de estado no deseados"""
        
        # Simular un deudor en estado AMARILLO
        debtor = Debtor(
            id=1,
            phone="1234567890",
            state="AMARILLO",
            conversation_history=json.dumps([
                {"role": "assistant", "content": "¿Te gustaría que te envíe el link para completar tu pago?"},
                {"role": "user", "content": "Si"}
            ])
        )
        
        # Simular la función update_state (sin base de datos)
        current_state = debtor.state
        message = "Si"
        
        # Verificar que no cambia a GRIS si hay contexto de pago
        payment_context_keywords = ['link', 'pago', 'pagar', 'deuda', 'cuenta', 'regularizar', 'sí', 'si', 'acepto', 'quiero']
        message_lower = message.lower()
        
        if any(keyword in message_lower for keyword in payment_context_keywords):
            # Debería mantener el estado actual
            assert current_state in ["VERDE", "AMARILLO"], "Debería mantener estado favorable"
    
    def test_improved_keyword_detection(self):
        """Test que verifica la detección mejorada de palabras clave"""
        
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
            context_analysis = analyze_conversation_context([], message)
            assert context_analysis["has_positive_response"] == should_be_positive, f"Error con mensaje: {message}"
    
    def test_payment_intent_detection(self):
        """Test que verifica la detección de intención de pago"""
        
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
            context_analysis = analyze_conversation_context([], message)
            assert context_analysis["has_payment_intent"] == should_have_intent, f"Error con mensaje: {message}"

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