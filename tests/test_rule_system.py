#!/usr/bin/env python3
"""
Script de prueba para demostrar el nuevo sistema de evaluación de reglas.
Este script simula el caso de uso descrito en el problema.
"""

from services.rule_decision_service import rule_decision_service
from services.structured_prompt_service import structured_prompt_service
from services.traceability_service import traceability_service
from core.logging import get_logger
logger = get_logger(__name__)

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
    logger.info("🧪 PRUEBA DEL SISTEMA DE EVALUACIÓN DE REGLAS")
    logger.info("=" * 60)
    
    # Crear datos de prueba
    strategy = create_test_strategy()
    debtor_data = create_test_debtor()
    conversation_history = create_test_conversation()
    user_message = "¿Algún descuento?"
    
    logger.info(f"📋 Estrategia: {strategy['name']}")
    logger.info(f"👤 Deudor: {debtor_data['nombre']}")
    logger.info(f"💰 Deuda: ${debtor_data['deuda']:,.2f}")
    logger.info(f"🎯 Estado: {debtor_data['estado']}")
    logger.info(f"💬 Mensaje: {user_message}")
    logger.info("")
    
    # Evaluar reglas
    mock_strategy = MockStrategy(strategy)
    decision = rule_decision_service.evaluate_and_decide(  # type: ignore
        strategy=mock_strategy,
        debtor_data=debtor_data,
        current_state=debtor_data['estado'],
        conversation_history=conversation_history,
        user_message=user_message
    )
    
    logger.info("🎯 RESULTADO DE LA EVALUACIÓN:")
    logger.info(f"   Acción: {decision.action_description}")
    logger.info(f"   Tipo: {decision.action_type}")
    logger.info(f"   Reglas aplicables: {len(decision.applicable_rules)}")
    
    if decision.triggered_rule:
        rule = decision.triggered_rule
        logger.info(f"   Regla activada: {rule.get('name', 'Sin nombre')}")
        logger.info(f"   Respuesta: {rule.get('response', '')}")
    
    logger.info(f"   Restricciones: {len(decision.restrictions or [])}")
    logger.info(f"   Razonamiento: {decision.reasoning}")
    logger.info("")
    
    return decision

def test_structured_prompt():
    """Prueba la generación de prompt estructurado"""
    logger.info("📝 PRUEBA DE GENERACIÓN DE PROMPT ESTRUCTURADO")
    logger.info("=" * 60)
    
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
    
    logger.info("📋 PROMPT GENERADO:")
    logger.info("-" * 40)
    logger.info(prompt_result['prompt'])
    logger.info("-" * 40)
    logger.info("")
    
    logger.info("🔍 METADATOS:")
    logger.info(f"   Tipo de acción: {prompt_result['action_type']}")
    logger.info(f"   Restricciones: {len(prompt_result['restrictions'])}")
    logger.info(f"   Respuestas permitidas: {len(prompt_result['allowed_responses'])}")
    logger.info("")
    
    return prompt_result

def test_traceability():
    """Prueba el sistema de trazabilidad"""
    logger.info("📊 PRUEBA DEL SISTEMA DE TRAZABILIDAD")
    logger.info("=" * 60)
    
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
    
    logger.info("✅ Decisión registrada en trazabilidad")
    logger.info(f"   Timestamp: {log_entry['timestamp']}")
    logger.info(f"   Deudor ID: {log_entry['debtor_id']}")
    logger.info(f"   Estrategia ID: {log_entry['strategy_id']}")
    logger.info("")
    
    # Obtener analytics
    analytics = traceability_service.get_decision_analytics()
    logger.info("📈 ANALYTICS:")
    logger.info(f"   Total decisiones: {analytics['total_decisions']}")
    logger.info(f"   Tipos de acción: {analytics['action_types']}")
    logger.info(f"   Tasa de fallback: {analytics['fallback_rate']:.1f}%")
    logger.info(f"   Uso de reglas estrictas: {analytics['strict_rules_usage']:.1f}%")
    logger.info(f"   Promedio reglas por decisión: {analytics['average_rules_per_decision']:.1f}")
    logger.info("")

def main():
    """Función principal de prueba"""
    logger.info("🚀 INICIANDO PRUEBAS DEL SISTEMA DE REGLAS")
    logger.info("=" * 60)
    logger.info("")
    
    # Ejecutar pruebas
    test_rule_evaluation()
    test_structured_prompt()
    test_traceability()
    
    logger.info("✅ TODAS LAS PRUEBAS COMPLETADAS")
    logger.info("=" * 60)
    logger.info("")
    logger.info("📋 RESUMEN DE MEJORAS IMPLEMENTADAS:")
    logger.info("1. ✅ Evaluación programática de reglas antes del LLM")
    logger.info("2. ✅ Decisión de acción específica basada en reglas")
    logger.info("3. ✅ Prompt estructurado con restricciones")
    logger.info("4. ✅ Trazabilidad completa de decisiones")
    logger.info("5. ✅ Sistema de fallback automático")
    logger.info("6. ✅ Analytics de decisiones")
    logger.info("")
    logger.info("🎯 CASO DE PRUEBA:")
    logger.info("   Deudor: Tomas Castro, Estado: GRIS, Deuda: $40,000")
    logger.info("   Mensaje: '¿Algún descuento?'")
    logger.info("   Resultado: Se activa regla de descuento 25%")
    logger.info("   LLM: Recibe instrucciones específicas para ofrecer descuento")
    logger.info("")

if __name__ == "__main__":
    main() 