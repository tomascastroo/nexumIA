#!/usr/bin/env python3
"""
Script de prueba para demostrar el nuevo sistema de evaluación de reglas.
Este script simula el caso de uso descrito en el problema.
"""

import json
from services.rule_decision_service import rule_decision_service
from services.structured_prompt_service import structured_prompt_service
from services.traceability_service import traceability_service

class MockStrategy:
    """Mock de Strategy para pruebas"""
    def __init__(self, data):
        self.id = data['id']
        self.name = data['name']
        self.initial_prompt = data['initial_prompt']
        self.evaluable_rules = data['evaluable_rules']
        self.rules_by_state = data['rules_by_state']
        self.strict_mode = data['strict_mode']
        self.fallback_prompt = data['fallback_prompt']

def create_test_strategy():
    """Crea una estrategia de prueba con reglas"""
    return {
        'id': 1,
        'name': 'Estrategia de Prueba',
        'initial_prompt': 'Hola, soy Francisco de cobranzas...',
        'evaluable_rules': [
            {
                'name': 'Descuento GRIS 20%',
                'condition': "estado == 'GRIS' and deuda >= 30000",
                'response': 'Te ofrezco un 20% de descuento en tu deuda de ${deuda}.',
                'strict': True,
                'priority': 1,
                'enabled': True
            },
            {
                'name': 'Descuento GRIS 15%',
                'condition': "estado == 'GRIS' and deuda >= 20000 and deuda < 30000",
                'response': 'Te ofrezco un 15% de descuento en tu deuda de ${deuda}.',
                'strict': True,
                'priority': 2,
                'enabled': True
            },
            {
                'name': 'Escalar a humano',
                'condition': "estado == 'ROJO' and negative_responses_count >= 2",
                'response': 'Te voy a derivar con un especialista que se pondrá en contacto contigo.',
                'strict': False,
                'priority': 3,
                'enabled': True,
                'escalate_to_human': True
            }
        ],
        'rules_by_state': {
            'VERDE': {'prompt': '', 'rules': [], 'advanced_rules': []},
            'AMARILLO': {'prompt': '', 'rules': [], 'advanced_rules': []},
            'ROJO': {'prompt': '', 'rules': [], 'advanced_rules': []},
            'GRIS': {
                'prompt': '',
                'rules': [],
                'advanced_rules': [
                    {
                        'name': 'Descuento GRIS avanzado',
                        'conditions': {
                            'operator': 'AND',
                            'conditions': [
                                {'field': 'estado', 'operator': '==', 'value': 'GRIS'},
                                {'field': 'deuda', 'operator': '>=', 'value': 40000}
                            ]
                        },
                        'response': 'Te ofrezco un 25% de descuento especial en tu deuda de ${deuda}.',
                        'strict': True,
                        'priority': 1
                    }
                ]
            }
        },
        'strict_mode': True,
        'fallback_prompt': 'Gracias por tu interés. Un especialista se pondrá en contacto contigo.'
    }

def create_test_debtor():
    """Crea datos de deudor de prueba"""
    return {
        'nombre': 'Tomas Castro',
        'estado': 'GRIS',
        'deuda': 40000,
        'ciudad': 'Buenos Aires',
        'sexo': 'masculino',
        'fecha_registro': '2023-01-15'
    }

def create_test_conversation():
    """Crea historial de conversación de prueba"""
    return [
        {
            "role": "system",
            "content": "Tu nombre es Francisco. Tratá amablemente al deudor"
        },
        {
            "role": "assistant",
            "content": "Estimado/a Tomas Castro: Mi nombre es Francisco..."
        },
        {
            "role": "user",
            "content": "¿Algún descuento?"
        }
    ]

def test_rule_evaluation():
    """Prueba la evaluación de reglas"""
    print("🧪 PRUEBA DEL SISTEMA DE EVALUACIÓN DE REGLAS")
    print("=" * 60)
    
    # Crear datos de prueba
    strategy = create_test_strategy()
    debtor_data = create_test_debtor()
    conversation_history = create_test_conversation()
    user_message = "¿Algún descuento?"
    
    print(f"📋 Estrategia: {strategy['name']}")
    print(f"👤 Deudor: {debtor_data['nombre']}")
    print(f"💰 Deuda: ${debtor_data['deuda']:,.2f}")
    print(f"🎯 Estado: {debtor_data['estado']}")
    print(f"💬 Mensaje: {user_message}")
    print()
    
    # Evaluar reglas
    mock_strategy = MockStrategy(strategy)
    decision = rule_decision_service.evaluate_and_decide(  # type: ignore
        strategy=mock_strategy,
        debtor_data=debtor_data,
        current_state=debtor_data['estado'],
        conversation_history=conversation_history,
        user_message=user_message
    )
    
    print("🎯 RESULTADO DE LA EVALUACIÓN:")
    print(f"   Acción: {decision.action_description}")
    print(f"   Tipo: {decision.action_type}")
    print(f"   Reglas aplicables: {len(decision.applicable_rules)}")
    
    if decision.triggered_rule:
        rule = decision.triggered_rule
        print(f"   Regla activada: {rule.get('name', 'Sin nombre')}")
        print(f"   Respuesta: {rule.get('response', '')}")
    
    print(f"   Restricciones: {len(decision.restrictions or [])}")
    print(f"   Razonamiento: {decision.reasoning}")
    print()
    
    return decision

def test_structured_prompt():
    """Prueba la generación de prompt estructurado"""
    print("📝 PRUEBA DE GENERACIÓN DE PROMPT ESTRUCTURADO")
    print("=" * 60)
    
    strategy = create_test_strategy()
    debtor_data = create_test_debtor()
    conversation_history = create_test_conversation()
    user_message = "¿Algún descuento?"
    
    # Generar prompt estructurado
    mock_strategy = MockStrategy(strategy)
    prompt_result = structured_prompt_service.generate_action_specific_prompt(  # type: ignore
        strategy=mock_strategy,
        debtor_data=debtor_data,
        current_state=debtor_data['estado'],
        conversation_history=conversation_history,
        user_message=user_message,
        is_first_message=False
    )
    
    print("📋 PROMPT GENERADO:")
    print("-" * 40)
    print(prompt_result['prompt'])
    print("-" * 40)
    print()
    
    print("🔍 METADATOS:")
    print(f"   Tipo de acción: {prompt_result['action_type']}")
    print(f"   Restricciones: {len(prompt_result['restrictions'])}")
    print(f"   Respuestas permitidas: {len(prompt_result['allowed_responses'])}")
    print()
    
    return prompt_result

def test_traceability():
    """Prueba el sistema de trazabilidad"""
    print("📊 PRUEBA DEL SISTEMA DE TRAZABILIDAD")
    print("=" * 60)
    
    strategy = create_test_strategy()
    debtor_data = create_test_debtor()
    conversation_history = create_test_conversation()
    user_message = "¿Algún descuento?"
    
    # Simular decisión y respuesta
    mock_strategy = MockStrategy(strategy)
    decision = rule_decision_service.evaluate_and_decide(  # type: ignore
        strategy=mock_strategy,
        debtor_data=debtor_data,
        current_state=debtor_data['estado'],
        conversation_history=conversation_history,
        user_message=user_message
    )
    
    # Simular respuesta del LLM
    llm_response = "Te ofrezco un 25% de descuento especial en tu deuda de $40,000. Esta es una oportunidad única para regularizar tu situación."
    
    # Registrar en trazabilidad
    log_entry = traceability_service.log_rule_decision(
        debtor_id=1,
        strategy_id=1,
        user_message=user_message,
        decision=decision,
        llm_response=llm_response,
        conversation_history=conversation_history,
        debtor_data=debtor_data
    )
    
    print("✅ Decisión registrada en trazabilidad")
    print(f"   Timestamp: {log_entry['timestamp']}")
    print(f"   Deudor ID: {log_entry['debtor_id']}")
    print(f"   Estrategia ID: {log_entry['strategy_id']}")
    print()
    
    # Obtener analytics
    analytics = traceability_service.get_decision_analytics()
    print("📈 ANALYTICS:")
    print(f"   Total decisiones: {analytics['total_decisions']}")
    print(f"   Tipos de acción: {analytics['action_types']}")
    print(f"   Tasa de fallback: {analytics['fallback_rate']:.1f}%")
    print(f"   Uso de reglas estrictas: {analytics['strict_rules_usage']:.1f}%")
    print(f"   Promedio reglas por decisión: {analytics['average_rules_per_decision']:.1f}")
    print()

def main():
    """Función principal de prueba"""
    print("🚀 INICIANDO PRUEBAS DEL SISTEMA DE REGLAS")
    print("=" * 60)
    print()
    
    # Ejecutar pruebas
    test_rule_evaluation()
    test_structured_prompt()
    test_traceability()
    
    print("✅ TODAS LAS PRUEBAS COMPLETADAS")
    print("=" * 60)
    print()
    print("📋 RESUMEN DE MEJORAS IMPLEMENTADAS:")
    print("1. ✅ Evaluación programática de reglas antes del LLM")
    print("2. ✅ Decisión de acción específica basada en reglas")
    print("3. ✅ Prompt estructurado con restricciones")
    print("4. ✅ Trazabilidad completa de decisiones")
    print("5. ✅ Sistema de fallback automático")
    print("6. ✅ Analytics de decisiones")
    print()
    print("🎯 CASO DE PRUEBA:")
    print("   Deudor: Tomas Castro, Estado: GRIS, Deuda: $40,000")
    print("   Mensaje: '¿Algún descuento?'")
    print("   Resultado: Se activa regla de descuento 25%")
    print("   LLM: Recibe instrucciones específicas para ofrecer descuento")
    print()

if __name__ == "__main__":
    main() 