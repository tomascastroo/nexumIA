import pytest
from services.payment_link_service import payment_link_service

def test_no_link_sin_identidad():
    debtor_data = {'deuda': 50000}
    conversation_history = []
    should_generate, reason, data = payment_link_service.should_generate_payment_link(
        user_message='Dame el link de pago',
        debtor_state='VERDE',
        conversation_history=conversation_history,
        debtor_data=debtor_data
    )
    assert not should_generate
    assert reason == 'IDENTITY_NOT_VALIDATED'

def test_link_estado_verde():
    debtor_data = {'dni': '12345678', 'deuda': 50000}
    conversation_history = [{'role': 'user', 'content': 'Mi DNI es 12345678'}]
    should_generate, reason, data = payment_link_service.should_generate_payment_link(
        user_message='Dame el link de pago',
        debtor_state='VERDE',
        conversation_history=conversation_history,
        debtor_data=debtor_data
    )
    assert should_generate
    assert reason == 'VERDE_STATE_IMMEDIATE'

def test_no_link_estado_rojo():
    debtor_data = {'dni': '12345678', 'deuda': 50000}
    conversation_history = [{'role': 'user', 'content': 'Mi DNI es 12345678'}]
    should_generate, reason, data = payment_link_service.should_generate_payment_link(
        user_message='Dame el link de pago',
        debtor_state='ROJO',
        conversation_history=conversation_history,
        debtor_data=debtor_data
    )
    assert not should_generate
    assert reason == 'ROJO_STATE_NO_AUTO_GENERATION' 