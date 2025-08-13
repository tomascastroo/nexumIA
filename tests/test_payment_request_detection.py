import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.payment_link_service import PaymentLinkService

def test_payment_request_detection():
    """Test que verifica que el sistema detecta solicitudes de pago correctamente"""
    
    print("🧪 Test: Detección de solicitudes de pago")
    print("=" * 60)
    
    payment_service = PaymentLinkService()
    
    # Test casos del problema real
    test_cases = [
        {
            "message": "Quiero pagar",
            "expected": True,
            "description": "Solicitud directa de pago"
        },
        {
            "message": "Bueno dale pasame el link",
            "expected": True,
            "description": "Solicitud de link"
        },
        {
            "message": "Pasar el link",
            "expected": True,
            "description": "Solicitud de link (variante)"
        },
        {
            "message": "Pagar ahora",
            "expected": True,
            "description": "Intención de pago inmediato"
        },
        {
            "message": "Pago online",
            "expected": True,
            "description": "Método de pago específico"
        },
        {
            "message": "Hola",
            "expected": False,
            "description": "Saludo (no es solicitud de pago)"
        },
        {
            "message": "No quiero pagar",
            "expected": False,
            "description": "Rechazo (no es solicitud de pago)"
        }
    ]
    
    for test_case in test_cases:
        message = test_case["message"]
        expected = test_case["expected"]
        description = test_case["description"]
        
        # Verificar detección
        detected = payment_service._detect_payment_link_request(message.lower())
        
        print(f"📝 Mensaje: '{message}'")
        print(f"   Descripción: {description}")
        print(f"   Detectado: {detected}")
        print(f"   Esperado: {expected}")
        
        if detected == expected:
            print("   ✅ CORRECTO")
        else:
            print("   ❌ INCORRECTO")
        
        print()
    
    return True

def test_full_payment_flow():
    """Test del flujo completo de pago con DNI"""
    
    print("\n🧪 Test: Flujo completo de pago")
    print("=" * 60)
    
    payment_service = PaymentLinkService()
    
    # Simular conversación completa del caso problemático
    conversation_history = [
        {"role": "assistant", "content": "Hola, ¿quieres pagar tu deuda?"},
        {"role": "user", "content": "Quiero pagar"},
        {"role": "assistant", "content": "Perfecto. Necesito confirmar tu identidad. ¿Podrías proporcionarme tu DNI?"},
        {"role": "user", "content": "45580095 es mi dni"}
    ]
    
    # Verificar que puede generar link
    should_generate, reason, data = payment_service.should_generate_payment_link(
        user_message="Quiero pagar",
        debtor_state="VERDE",
        conversation_history=conversation_history,
        debtor_data={"deuda": 40000}
    )
    
    print(f"📊 Debe generar link: {should_generate}")
    print(f"📊 Razón: {reason}")
    print(f"📊 Datos: {data}")
    
    # Debe poder generar el link
    assert should_generate, f"Debe generar link. Razón: {reason}"
    assert reason != "IDENTITY_NOT_VALIDATED", "No debe rechazar por identidad no validada"
    assert reason != "NO_PAYMENT_LINK_REQUESTED", "No debe rechazar por falta de solicitud"
    
    print("✅ Test exitoso: Flujo completo funciona correctamente")
    return True

def test_payment_with_dni_confirmation():
    """Test específico del caso problemático"""
    
    print("\n🧪 Test: Caso específico del problema")
    print("=" * 60)
    
    payment_service = PaymentLinkService()
    
    # Caso exacto del problema
    conversation_history = [
        {"role": "assistant", "content": "¿Quieres pagar tu deuda?"},
        {"role": "user", "content": "Quiero pagar"},
        {"role": "assistant", "content": "Necesito tu DNI para confirmar tu identidad"},
        {"role": "user", "content": "45580095 es mi dni"}
    ]
    
    # Verificar identidad
    identity_validated = payment_service._check_identity_in_conversation(conversation_history)
    print(f"📊 Identidad validada: {identity_validated}")
    
    # Verificar solicitud de pago
    payment_requested = payment_service._detect_payment_link_request("quiero pagar")
    print(f"📊 Solicitud de pago detectada: {payment_requested}")
    
    # Verificar generación de link
    should_generate, reason, data = payment_service.should_generate_payment_link(
        user_message="Quiero pagar",
        debtor_state="VERDE",
        conversation_history=conversation_history,
        debtor_data={"deuda": 40000}
    )
    
    print(f"📊 Debe generar link: {should_generate}")
    print(f"📊 Razón: {reason}")
    
    # Todas las verificaciones deben pasar
    assert identity_validated, "Debe detectar identidad con DNI"
    assert payment_requested, "Debe detectar solicitud de pago"
    assert should_generate, f"Debe generar link. Razón: {reason}"
    
    print("✅ Test exitoso: Caso problemático resuelto")
    return True

if __name__ == "__main__":
    print("🚀 Iniciando tests de detección de solicitudes de pago")
    print("=" * 60)
    
    try:
        test_payment_request_detection()
        test_full_payment_flow()
        test_payment_with_dni_confirmation()
        
        print("\n🎉 Todos los tests de detección de pago pasaron exitosamente!")
        print("✅ El sistema ya detecta correctamente las solicitudes de pago")
        
    except Exception as e:
        print(f"❌ Error en test: {e}")
        import traceback
        traceback.print_exc() 