from sqlalchemy.orm import Session
from models.Debtor import Debtor
from services.debtor_service import update_state
from services.openai_service import generate_openai_response_sync
from services.whatsapp_service import send_whatsapp_message

from sqlalchemy.orm import Session
from models.Debtor import Debtor
from services.debtor_service import update_state
from services.openai_service import generate_openai_response_sync
from services.whatsapp_service import send_whatsapp_message

async def handle_incoming_message(phone: str, body: str, db: Session):
    debtor = db.query(Debtor).filter(Debtor.phone == phone).first()
    if not debtor:
        return  # No deudor encontrado

    history = debtor.conversation_history or []
    history.append({"role": "user", "content": body})

    # 1. Clasificamos el nuevo estado de intención
    new_state = update_state(history)
    debtor.state = new_state

    # 2. Armamos el prompt según estado
    strategy = debtor.campaign.strategy.rules
    base_prompt = strategy.get("prompt", "")
    rules_by_state = strategy.get("rules_by_state", {})
    rules_for_state = rules_by_state.get(new_state, "No hay reglas definidas para este estado.")

    system_prompt = f"""
Sos un agente de cobranzas profesional. Seguí estas reglas según el estado actual del deudor.

Estado del deudor: {new_state}

Reglas:
{rules_for_state}

{base_prompt}
    """.strip()

    # 3. Agregamos el prompt como primer mensaje "system"
    messages = [{"role": "system", "content": system_prompt}] + history

    # 4. Generamos respuesta y actualizamos todo
    response = generate_openai_response_sync(messages)

    history.append({"role": "assistant", "content": response})
    debtor.conversation_history = history
    db.commit()

    send_whatsapp_message(f"whatsapp:{phone}", response)
