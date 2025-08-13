import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.payment_link_service import PaymentLinkService

def test_identity_validation_with_dni():
    """Test que verifica que el payment link service detecta identidad con DNI"""
    
    print("🧪 Test: Payment Link Service - Detección de identidad con DNI")
    print("=" * 60)
    
    payment_service = PaymentLinkService()
    
    # Simular conversación donde el deudor proporciona DNI
    conversation_history = [
        {"role": "assistant", "content": "Hola, necesito confirmar tu identidad. ¿Podrías proporcionarme tu DNI?"},
        {"role": "user", "content": "45580095"},  # DNI del caso problemático
        {"role": "assistant", "content": "Gracias. ¿Quieres que te envíe el link de pago?"},
        {"role": "user", "content": "Si, dame el link"}
    ]
    
    # Verificar que detecta la identidad
    identity_validated = payment_service._check_identity_in_conversation(conversation_history)
    
    print(f"📊 Identidad validada: {identity_validated}")
    
    # Debe detectar la identidad
    assert identity_validated, "Debe detectar identidad cuando se proporciona DNI"
    
    # Verificar que puede generar link de pago
    should_generate, reason, data = payment_service.should_generate_payment_link(
        user_message="Si, dame el link",
        debtor_state="VERDE",
        conversation_history=conversation_history,
        debtor_data={"deuda": 40000}
    )
    
    print(f"📊 Debe generar link: {should_generate}")
    print(f"📊 Razón: {reason}")
    
    # Debe poder generar el link
    assert should_generate, f"Debe generar link cuando identidad está validada. Razón: {reason}"
    assert reason != "IDENTITY_NOT_VALIDATED", "No debe rechazar por identidad no validada"
    
    print("✅ Test exitoso: Payment link service detecta identidad correctamente")
    return True

def test_different_dni_formats():
    """Test diferentes formatos de DNI en payment link service"""
    
    print("\n🧪 Test: Diferentes formatos de DNI")
    print("=" * 60)
    
    payment_service = PaymentLinkService()
    
    dni_test_cases = [
        "45580095",  # DNI del caso problemático
        "12345678",  # DNI típico argentino
        "98765432",  # Otro DNI
        "1234567",   # DNI corto (debe ser >= 7)
        "123456789", # DNI largo
    ]
    
    for dni in dni_test_cases:
        conversation_history = [
            {"role": "assistant", "content": "¿Podrías proporcionarme tu DNI?"},
            {"role": "user", "content": dni}
        ]
        
        identity_validated = payment_service._check_identity_in_conversation(conversation_history)
        
        if len(dni) >= 7:
            # DNI válido debe detectar identidad
            assert identity_validated, f"DNI {dni} debe detectar identidad"
            print(f"✅ DNI {dni}: Identidad detectada")
        else:
            # DNI muy corto no debe detectar
            print(f"⚠️  DNI {dni}: Muy corto, no detectado")
    
    return True

def test_identity_with_phrases():
    """Test identidad con frases que contienen DNI"""
    
    print("\n🧪 Test: Frases con DNI")
    print("=" * 60)
    
    payment_service = PaymentLinkService()
    
    test_phrases = [
        "Mi DNI es 45580095",
        "Mi documento es 12345678",
        "Te envío mi DNI: 98765432",
        "Aquí está mi documento: 45678912"
    ]
    
    for phrase in test_phrases:
        conversation_history = [
            {"role": "assistant", "content": "¿Podrías confirmar tu identidad?"},
            {"role": "user", "content": phrase}
        ]
        
        identity_validated = payment_service._check_identity_in_conversation(conversation_history)
        
        # Debe detectar identidad en todas las frases
        assert identity_validated, f"Frase '{phrase}' debe detectar identidad"
        print(f"✅ Frase: '{phrase}' - Identidad detectada")
    
    return True

if __name__ == "__main__":
    print("🚀 Iniciando tests de payment link service")
    print("=" * 60)
    
    try:
        test_identity_validation_with_dni()
        test_different_dni_formats()
        test_identity_with_phrases()
        
        print("\n🎉 Todos los tests de payment link service pasaron exitosamente!")
        print("✅ El sistema ya detecta identidad correctamente y puede generar links")
        
    except Exception as e:
        print(f"❌ Error en test: {e}")
        import traceback
        traceback.print_exc() 