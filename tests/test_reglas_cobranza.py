import pytest
from services.rule_decision_service import rule_decision_service

class MockStrategy:
    def __init__(self, data):
        self.id = data['id']
        self.name = data['name']
        self.initial_prompt = data.get('initial_prompt', '')
        self.evaluable_rules = data.get('evaluable_rules', [])
        self.rules_by_state = data.get('rules_by_state', {})
        self.strict_mode = data.get('strict_mode', False)
        self.fallback_prompt = data.get('fallback_prompt', '')

def test_descuento_por_estado():
    strategy = {
        'id': 1,
        'name': 'Cobranza',
        'evaluable_rules': [
            {'name': 'Descuento GRIS', 'condition': "estado == 'GRIS' and deuda >= 30000", 'response': 'Te ofrezco un 20% de descuento.', 'strict': True, 'priority': 1, 'enabled': True}
        ],
        'rules_by_state': {},
        'strict_mode': True,
        'fallback_prompt': 'Un especialista se pondrá en contacto.'
    }
    debtor_data = {'estado': 'GRIS', 'deuda': 40000}
    decision = rule_decision_service.evaluate_and_decide(MockStrategy(strategy), debtor_data, 'GRIS', [], 'Quiero pagar')
    assert decision.action_type == 'offer_discount'
    assert 'descuento' in decision.triggered_rule['response'].lower()

def test_cierre_de_caso():
    strategy = {
        'id': 2,
        'name': 'Cobranza',
        'evaluable_rules': [
            {'name': 'Cerrar caso', 'condition': "estado == 'VERDE' and deuda == 0", 'response': 'Caso cerrado.', 'close_case': True, 'priority': 1, 'enabled': True}
        ],
        'rules_by_state': {},
        'strict_mode': False,
        'fallback_prompt': 'Un especialista se pondrá en contacto.'
    }
    debtor_data = {'estado': 'VERDE', 'deuda': 0}
    decision = rule_decision_service.evaluate_and_decide(MockStrategy(strategy), debtor_data, 'VERDE', [], 'Gracias')
    assert decision.action_type == 'close_case'
    assert 'cerrado' in decision.triggered_rule['response'].lower()

def test_negociacion():
    strategy = {
        'id': 3,
        'name': 'Cobranza',
        'evaluable_rules': [
            {'name': 'Negociar', 'condition': "estado == 'AMARILLO' and deuda > 10000", 'response': 'Podemos negociar un plan.', 'priority': 1, 'enabled': True}
        ],
        'rules_by_state': {},
        'strict_mode': False,
        'fallback_prompt': 'Un especialista se pondrá en contacto.'
    }
    debtor_data = {'estado': 'AMARILLO', 'deuda': 20000}
    decision = rule_decision_service.evaluate_and_decide(MockStrategy(strategy), debtor_data, 'AMARILLO', [], '¿Puedo pagar en cuotas?')
    assert decision.action_type == 'offer_payment_plan'
    assert 'negociar' in decision.triggered_rule['response'].lower() 