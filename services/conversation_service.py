from sqlalchemy.orm import Session, joinedload
from models.Debtor import Debtor
from models.Campaign import Campaign
from models.DebtorDataset import DebtorDataset
from models.Strategy import Strategy
from services.debtor_service import update_state
from services.openai_service import generate_openai_response_sync
from services.whatsapp_service import send_whatsapp_message
import json
from typing import List, Dict, Any, Optional, cast 
from openai.types.chat import ChatCompletionMessageParam, ChatCompletionSystemMessageParam, ChatCompletionUserMessageParam, ChatCompletionAssistantMessageParam

async def handle_incoming_message(phone: str, body: str, db: Session):
    # Eagerly load debtor_dataset, campaigns, and strategies to avoid AttributeError
    debtor = db.query(Debtor).options(
        joinedload(Debtor.debtor_dataset).joinedload(DebtorDataset.campaigns).joinedload(Campaign.strategy)
    ).filter(Debtor.phone == phone).first()
    if not debtor:
        return  # No deudor encontrado

    # Ensure current_history is a Python list, deserializing if it's a JSON string
    current_history_raw = debtor.conversation_history
    if current_history_raw is None:
        current_history: List[Dict[str, str]] = []
    elif isinstance(current_history_raw, str):
        try:
            current_history = json.loads(current_history_raw)
            if not isinstance(current_history, list):
                current_history = [] # Fallback if JSON is not a list
        except json.JSONDecodeError:
            current_history = []
    else:
        current_history = cast(List[Dict[str, str]], current_history_raw)

    current_history.append({"role": "user", "content": body})

    new_state = update_state(db, debtor.id, body)
    debtor.state = cast(str, new_state) # Cast to str for linter, ORM handles type

    # Normalize incoming message body for keyword matching
    normalized_body = body.lower().strip().replace("?", "") # Remove question mark as well

    # Check for debt inquiry intent
    debt_inquiry_keywords = [
        "cuanto debo",
        "cual es mi saldo",
        "cuanto tengo que pagar",
        "cuanto es la deuda",
        "monto de la deuda",
        "mi deuda",
        "de cuanto es el monto",
        "cuanto es el monto",
        "monto",
        "que debo",
        "mi saldo",
        "de cuanto es" # Added for user's query without question mark
    ]
    is_debt_inquiry = any(keyword in normalized_body for keyword in debt_inquiry_keywords)

    print(f"[DEBUG] Incoming message body (original): {body}")
    print(f"[DEBUG] Incoming message body (normalized): {normalized_body}")
    print(f"[DEBUG] Is debt inquiry: {is_debt_inquiry}")

    if is_debt_inquiry and debtor.custom_data is not None:
        print("[DEBUG] Debt inquiry detected and debtor.custom_data exists.")
        current_custom_data = cast(Dict[str, Any], debtor.custom_data) if debtor.custom_data is not None else {}

        print(f"[DEBUG] Debtor custom_data: {current_custom_data}")
        debt_amount_raw = current_custom_data.get("deuda")
        
        # Attempt to convert debt_amount to a float, handling potential errors
        debt_amount: Optional[float] = None
        if debt_amount_raw is not None:
            try:
                debt_amount = float(debt_amount_raw)
            except (ValueError, TypeError):
                print(f"[DEBUG] Could not convert debt_amount_raw ({debt_amount_raw}) to float.")

        print(f"[DEBUG] Debt amount from custom_data (after conversion attempt): {debt_amount}, type: {type(debt_amount)}")

        if isinstance(debt_amount, (int, float)):
            print("[DEBUG] Debt amount is a valid number. Preparing direct response.")
            response_text = f"Tu deuda es de ${debt_amount:,.2f}".replace(",", ".") # Format with 2 decimal places and use dot for thousands separator
            current_history.append({"role": "assistant", "content": response_text})
            debtor.conversation_history = cast(List[Dict[str, str]], current_history)
            db.commit()
            # send_whatsapp_message(f"whatsapp:{phone}", response_text) # REMOVED
            print("[DEBUG] Direct debt response generated. Returning.")
            return response_text # Return the response text
        else:
            print("[DEBUG] Debt amount not a valid number or not found. Falling back to LLM.")

    # Original LLM prompt generation logic for other intents
    strategy_rules = {}
    active_campaign: Optional[Campaign] = None

    if debtor.debtor_dataset and debtor.debtor_dataset.campaigns:
        # Find an active campaign for the debtor's dataset
        for campaign_obj in debtor.debtor_dataset.campaigns:
            # Assuming 'active' is the relevant status for a conversational campaign
            # You might need more sophisticated logic here if multiple campaigns can be active or if there's a priority
            if campaign_obj.status == "active" and campaign_obj.strategy:
                active_campaign = campaign_obj
                break

    if active_campaign and active_campaign.strategy:
        strategy_rules = cast(Dict[str, Any], active_campaign.strategy.rules)
    else:
        print("[DEBUG] No active campaign or strategy found for this debtor's dataset. Using default/empty prompt rules.")
        # Fallback if no active campaign or strategy found, base_prompt and rules_for_state will use defaults

    base_prompt = strategy_rules.get("prompt", "")
    rules_by_state = strategy_rules.get("rules_by_state", {})
    rules_for_state = rules_by_state.get(new_state, "No hay reglas definidas para este estado.")

    custom_data_str = ""
    current_custom_data_for_llm = cast(Dict[str, Any], debtor.custom_data) if debtor.custom_data is not None else {}

    if current_custom_data_for_llm:
        custom_data_str = "\nDatos del Deudor:\n"
        for key, value in current_custom_data_for_llm.items():
            custom_data_str += f"- {key}: {value}\n"

    system_prompt = f"""
Sos un agente de cobranzas profesional. Seguí estas reglas según el estado actual del deudor.

Estado del deudor: {new_state}

Reglas:
{rules_for_state}

{base_prompt}

INSTRUCCIÓN CLAVE: Es *CRÍTICO* que utilices y consultes *siempre* los 'Datos del Deudor' proporcionados a continuación para personalizar y basar *todas* tus respuestas. Prioriza el uso de la información específica del deudor para hacer tus respuestas relevantes y personalizadas. Si el deudor pregunta por información específica que está en sus Datos del Deudor, refiérete directamente a esa información. **Bajo ninguna circunstancia debes generar un placeholder como '[monto deuda]' o '[valor deuda]'. Siempre debes intentar usar el valor numérico real de la deuda si está disponible en 'Datos del Deudor' para cualquier contexto, pero la respuesta sobre el monto exacto será manejada por el sistema.**

{custom_data_str}
    """.strip()

    messages: List[ChatCompletionMessageParam] = [ChatCompletionSystemMessageParam(role="system", content=system_prompt)]

    for msg in current_history:
        if msg['role'] == 'user':
            messages.append(ChatCompletionUserMessageParam(role="user", content=msg['content']))
        elif msg['role'] == 'assistant':
            messages.append(ChatCompletionAssistantMessageParam(role="assistant", content=msg['content']))

    response = generate_openai_response_sync(messages)

    current_history.append({"role": "assistant", "content": response})
    debtor.conversation_history = cast(List[Dict[str, str]], current_history) # Cast to List[Dict] for linter, ORM handles type
    db.commit()

    # send_whatsapp_message(f"whatsapp:{phone}", response) # REMOVED
    print("[DEBUG] LLM response generated. Returning.")
    return response # Return the response text
