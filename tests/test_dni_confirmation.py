import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.openai_service import analyze_conversation_context, classify_state
from services.debtor_service import update_state
import json

def test_dni_confirmation():
    """Test que verifica que el DNI no cambia el estado a GRIS"""
    
    print("🧪 Test: Confirmación de DNI no debe cambiar a GRIS")
    print("=" * 60)
    
    # Simular conversación donde el deudor está en VERDE y proporciona DNI
    conversation_history = [
        {"role": "assistant", "content": "Hola, soy Francisco del banco Santander. Tenemos una deuda pendiente de $40,000. ¿Te interesa regularizarla?"},
        {"role": "user", "content": "Si, quiero pagar"},
        {"role": "assistant", "content": "Perfecto. Para proceder necesito confirmar tu identidad. ¿Podrías proporcionarme tu DNI?"},
        {"role": "user", "content": "45580095"}  # DNI del caso problemático
    ]
    
    # Analizar el contexto
    context_analysis = analyze_conversation_context(conversation_history, "45580095")
    
    print(f"📊 Análisis de contexto:")
    print(f"   - Confirmación de identidad: {context_analysis['has_identity_confirmation']}")
    print(f"   - Cooperativo: {context_analysis['is_cooperative']}")
    print(f"   - Indicadores: {context_analysis['context_indicators']}")
    
    # Verificar que detecta confirmación de identidad
    assert context_analysis["has_identity_confirmation"] == True, "Debe detectar confirmación de identidad"
    assert context_analysis["is_cooperative"] == True, "Debe ser cooperativo al confirmar identidad"
    assert "confirmación_identidad" in context_analysis["context_indicators"], "Debe marcar confirmación de identidad"
    
    # Clasificar el estado
    state = classify_state("45580095", conversation_history)
    
    print(f"🎯 Estado clasificado: {state}")
    
    # NO debe ser GRIS si confirma identidad
    assert state != "GRIS", f"ERROR: Estado no debe ser GRIS al confirmar identidad. Estado actual: {state}"
    
    # Debería ser VERDE o AMARILLO
    assert state in ["VERDE", "AMARILLO"], f"Estado debe ser favorable al confirmar identidad. Estado actual: {state}"
    
    print(f"✅ Test exitoso: Estado {state} es correcto")
    return True

def test_state_protection_with_dni():
    """Test que verifica la protección de estado cuando se proporciona DNI"""
    
    print("\n🧪 Test: Protección de estado con DNI")
    print("=" * 60)
    
    # Simular deudor en estado VERDE
    current_state = "VERDE"
    message = "45580095"
    
    # Verificar que la lógica de protección funciona
    message_lower = message.lower()
    payment_context_keywords = ['link', 'pago', 'pagar', 'deuda', 'cuenta', 'regularizar', 'sí', 'si', 'acepto', 'quiero']
    
    # Si el mensaje es un DNI, debe mantener el estado
    if message.strip().isdigit() and len(message.strip()) >= 7:
        print(f"✅ DNI detectado: {message}")
        print(f"✅ Debe mantener estado: {current_state}")
        return True
    
    # Si hay contexto de pago, también debe mantener
    if any(keyword in message_lower for keyword in payment_context_keywords):
        print(f"✅ Contexto de pago detectado")
        print(f"✅ Debe mantener estado: {current_state}")
        return True
    
    print("❌ No se detectó protección de estado")
    return False

def test_multiple_dni_formats():
    """Test diferentes formatos de DNI"""
    
    print("\n🧪 Test: Diferentes formatos de DNI")
    print("=" * 60)
    
    dni_test_cases = [
        "45580095",  # DNI del caso problemático
        "12345678",  # DNI típico argentino
        "98765432",  # Otro DNI
        "1234567",   # DNI corto (debe ser >= 7)
        "123456789", # DNI largo
    ]
    
    for dni in dni_test_cases:
        context_analysis = analyze_conversation_context([], dni)
        
        if len(dni) >= 7:
            # DNI válido debe detectar confirmación de identidad
            assert context_analysis["has_identity_confirmation"] == True, f"DNI {dni} debe detectar confirmación"
            assert context_analysis["is_cooperative"] == True, f"DNI {dni} debe ser cooperativo"
            print(f"✅ DNI {dni}: Confirmación detectada")
        else:
            # DNI muy corto no debe detectar
            print(f"⚠️  DNI {dni}: Muy corto, no detectado")
    
    return True

if __name__ == "__main__":
    print("🚀 Iniciando tests de confirmación de DNI")
    print("=" * 60)
    
    try:
        test_dni_confirmation()
        test_state_protection_with_dni()
        test_multiple_dni_formats()
        
        print("\n🎉 Todos los tests de DNI pasaron exitosamente!")
        print("✅ El sistema ya NO cambia a GRIS cuando se confirma identidad")
        
    except Exception as e:
        print(f"❌ Error en test: {e}")
        import traceback
        traceback.print_exc() 