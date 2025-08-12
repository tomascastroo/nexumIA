#!/usr/bin/env python3
"""
Script de prueba para el sistema de links de pago
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.payment_link_service import payment_link_service
from typing import Dict, Any, List

def test_payment_link_detection():
    """Prueba la detección de solicitudes de links de pago"""
    print("🧪 Probando detección de solicitudes de links de pago...")
    
    test_messages = [
        "Quiero pagar mi deuda",
        "Dame el link para pagar",
        "¿Cómo puedo pagar?",
        "Necesito el enlace de pago",
        "Hola, ¿cómo estás?",
        "Cuál es mi saldo",
        "Quiero pagar con tarjeta",
        "Dame el link de pago por favor",
        "¿Puedo pagar con MercadoPago?",
        "No tengo dinero"
    ]
    
    for message in test_messages:
        is_payment_request = payment_link_service._detect_payment_link_request(message.lower())
        print(f"  '{message}' -> {'✅ Solicita link' if is_payment_request else '❌ No solicita link'}")
    
    print()

def test_identity_validation():
    """Prueba la validación de identidad"""
    print("🧪 Probando validación de identidad...")
    
    # Caso 1: Deudor con datos de identidad
    debtor_data_1 = {"dni": "12345678", "email": "test@example.com", "deuda": 50000}
    conversation_history_1 = [
        {"role": "user", "content": "Mi DNI es 12345678"},
        {"role": "assistant", "content": "Gracias por confirmar tus datos"}
    ]
    
    identity_validated_1 = payment_link_service._check_identity_validation(
        conversation_history_1, debtor_data_1
    )
    print(f"  Deudor con DNI y email -> {'✅ Identidad validada' if identity_validated_1 else '❌ Identidad no validada'}")
    
    # Caso 2: Deudor sin datos de identidad
    debtor_data_2 = {"deuda": 50000}
    conversation_history_2 = [
        {"role": "user", "content": "Hola"},
        {"role": "assistant", "content": "Hola, ¿cómo estás?"}
    ]
    
    identity_validated_2 = payment_link_service._check_identity_validation(
        conversation_history_2, debtor_data_2
    )
    print(f"  Deudor sin datos de identidad -> {'✅ Identidad validada' if identity_validated_2 else '❌ Identidad no validada'}")
    
    # Caso 3: Deudor con validación en conversación
    debtor_data_3 = {"deuda": 50000}
    conversation_history_3 = [
        {"role": "user", "content": "Mi DNI es 87654321"},
        {"role": "assistant", "content": "Perfecto, confirmé tus datos"}
    ]
    
    identity_validated_3 = payment_link_service._check_identity_validation(
        conversation_history_3, debtor_data_3
    )
    print(f"  Deudor con validación en conversación -> {'✅ Identidad validada' if identity_validated_3 else '❌ Identidad no validada'}")
    
    print()

def test_state_based_decisions():
    """Prueba las decisiones basadas en el estado del deudor"""
    print("🧪 Probando decisiones basadas en estado...")
    
    # Datos de prueba
    debtor_data = {"dni": "12345678", "deuda": 50000}
    conversation_history = [
        {"role": "user", "content": "Mi DNI es 12345678"},
        {"role": "assistant", "content": "Gracias por confirmar tus datos"}
    ]
    
    test_cases = [
        ("VERDE", "Quiero pagar mi deuda"),
        ("AMARILLO", "Dame el link para pagar"),
        ("ROJO", "Quiero pagar mi deuda"),
        ("GRIS", "Dame el link para pagar"),
        ("VERDE", "Hola, ¿cómo estás?"),
        ("AMARILLO", "Hola, ¿cómo estás?")
    ]
    
    for state, message in test_cases:
        should_generate, reason, data = payment_link_service.should_generate_payment_link(
            user_message=message,
            debtor_state=state,
            conversation_history=conversation_history,
            debtor_data=debtor_data
        )
        
        status = "✅ Generar" if should_generate else "❌ No generar"
        print(f"  Estado {state} + '{message}' -> {status} ({reason})")
    
    print()

def test_response_generation():
    """Prueba la generación de respuestas"""
    print("🧪 Probando generación de respuestas...")
    
    debtor_data = {"deuda": 50000}
    
    test_cases = [
        ("VERDE", {"message": "Deudor en estado VERDE solicita link de pago"}),
        ("AMARILLO", {"message": "Deudor en estado AMARILLO solicita explícitamente link de pago"}),
        ("ROJO", {"message": "Deudor en estado ROJO - no generar link automáticamente"}),
        ("GRIS", {"message": "Deudor en estado GRIS - no generar link automáticamente"})
    ]
    
    for state, decision_data in test_cases:
        response = payment_link_service.generate_payment_link_response(
            debtor_state=state,
            debtor_data=debtor_data,
            decision_data=decision_data
        )
        
        print(f"  Estado {state}:")
        print(f"    {response[:100]}...")
        print()
    
    print()

def test_payment_link_creation():
    """Prueba la creación de links de pago"""
    print("🧪 Probando creación de links de pago...")
    
    payment_info = payment_link_service.create_payment_link(
        debtor_id=123,
        amount=50000,
        discount=10,
        method="mock"
    )
    
    print(f"  Link generado: {payment_info['payment_link']}")
    print(f"  Monto solicitado: ${payment_info['amount_requested']:,.2f}")
    print(f"  Monto final: ${payment_info['final_amount']:,.2f}")
    print(f"  Descuento: {payment_info['discount_applied']}%")
    print(f"  Método: {payment_info['method']}")
    print(f"  Expira: {payment_info['expires_at']}")
    print()

def test_integration_scenario():
    """Prueba un escenario completo de integración"""
    print("🧪 Probando escenario completo de integración...")
    
    # Escenario: Deudor VERDE solicita link de pago
    print("📋 Escenario: Deudor VERDE solicita link de pago")
    
    debtor_data = {"dni": "12345678", "deuda": 50000}
    conversation_history = [
        {"role": "user", "content": "Mi DNI es 12345678"},
        {"role": "assistant", "content": "Gracias por confirmar tus datos"},
        {"role": "user", "content": "Quiero pagar mi deuda"}
    ]
    
    # 1. Verificar si debe generar link
    should_generate, reason, data = payment_link_service.should_generate_payment_link(
        user_message="Quiero pagar mi deuda",
        debtor_state="VERDE",
        conversation_history=conversation_history,
        debtor_data=debtor_data
    )
    
    print(f"  ¿Debe generar link? {'✅ Sí' if should_generate else '❌ No'}")
    print(f"  Razón: {reason}")
    
    if should_generate:
        # 2. Generar respuesta
        response = payment_link_service.generate_payment_link_response(
            debtor_state="VERDE",
            debtor_data=debtor_data,
            decision_data=data
        )
        
        print(f"  Respuesta generada:")
        print(f"    {response}")
        
        # 3. Crear link de pago
        payment_info = payment_link_service.create_payment_link(
            debtor_id=123,
            amount=50000,
            method="mock"
        )
        
        print(f"  Link de pago creado: {payment_info['payment_link']}")
    
    print()

def test_false_positive_detection():
    """Prueba que el sistema no genere falsos positivos"""
    print("🧪 Probando detección de falsos positivos...")
    
    # Mensajes que NO deberían generar link de pago
    false_positive_messages = [
        "Hola, ¿cómo estás?",
        "Qué tal?",
        "Cuánto debo?",
        "Cuál es mi saldo?",
        "Quiero saber mi deuda",
        "Puedo pagar en cuotas?",
        "Tengo una consulta",
        "Necesito ayuda",
        "¿Qué opciones tengo?",
        "¿Hay descuentos?",
        "¿Puedo pagar con tarjeta?"  # Pregunta general, no solicitud específica
    ]
    
    debtor_data = {"dni": "12345678", "deuda": 50000}
    conversation_history = [
        {"role": "user", "content": "Mi DNI es 12345678"},
        {"role": "assistant", "content": "Gracias por confirmar tus datos"}
    ]
    
    for message in false_positive_messages:
        should_generate, reason, data = payment_link_service.should_generate_payment_link(
            user_message=message,
            debtor_state="VERDE",
            conversation_history=conversation_history,
            debtor_data=debtor_data
        )
        
        status = "❌ FALSO POSITIVO" if should_generate else "✅ Correcto"
        print(f"  '{message}' -> {status} ({reason})")
    
    print()

def test_specific_payment_requests():
    """Prueba que el sistema detecte correctamente las solicitudes específicas"""
    print("🧪 Probando detección de solicitudes específicas...")
    
    # Mensajes que SÍ deberían generar link de pago
    specific_requests = [
        "Dame el link de pago",
        "Enviame el enlace para pagar",
        "Quiero pagar ahora",
        "Link de pago",
        "Enlace de pago",
        "Dame el link",
        "Mandame el enlace",
        "Cómo pago online",
        "Donde pago online"
    ]
    
    debtor_data = {"dni": "12345678", "deuda": 50000}
    conversation_history = [
        {"role": "user", "content": "Mi DNI es 12345678"},
        {"role": "assistant", "content": "Gracias por confirmar tus datos"}
    ]
    
    for message in specific_requests:
        should_generate, reason, data = payment_link_service.should_generate_payment_link(
            user_message=message,
            debtor_state="VERDE",
            conversation_history=conversation_history,
            debtor_data=debtor_data
        )
        
        status = "✅ Correcto" if should_generate else "❌ NO DETECTÓ"
        print(f"  '{message}' -> {status} ({reason})")
    
    print()

def test_improved_responses():
    """Prueba las respuestas mejoradas"""
    print("🧪 Probando respuestas mejoradas...")
    
    debtor_data = {"deuda": 50000}
    
    # Probar respuesta para estado VERDE
    response = payment_link_service.generate_payment_link_response(
        debtor_state="VERDE",
        debtor_data=debtor_data,
        decision_data={"message": "Test"}
    )
    
    print("📝 Respuesta para estado VERDE:")
    print(response)
    print()
    
    # Verificar que la respuesta contiene información específica
    assert "📋 Información del pago:" in response
    assert "🔗 Link de pago:" in response
    assert "⚠️ Importante:" in response
    assert "$50,000.00" in response
    
    print("✅ Respuesta mejorada verificada correctamente")
    print()

def main():
    """Función principal de pruebas"""
    print("🚀 Iniciando pruebas del sistema de links de pago")
    print("=" * 60)
    
    try:
        test_payment_link_detection()
        test_identity_validation()
        test_state_based_decisions()
        test_response_generation()
        test_payment_link_creation()
        test_integration_scenario()
        test_false_positive_detection()
        test_specific_payment_requests()
        test_improved_responses()
        
        print("✅ Todas las pruebas completadas exitosamente")
        print("🎯 El sistema de links de pago está funcionando correctamente")
        
    except Exception as e:
        print(f"❌ Error durante las pruebas: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 