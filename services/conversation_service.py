from sqlalchemy.orm import Session, joinedload
from typing import Any, Dict, Optional, List, cast
from db.db import SessionLocal
from models.Debtor import Debtor
from services import openai_service
from schemas.conversation import Conversation, ConversationUpdate

# Nueva API unificada de conversación
def start_conversation(bot_id: int, debtor_id: int, context: Optional[Dict[str, Any]] = None) -> Conversation:
    """Inicializa una conversación para un deudor y retorna su estado y el historial inicial."""
    db: Session = SessionLocal()
    try:
        debtor = db.query(Debtor).filter(Debtor.id == debtor_id).first()
        if not debtor:
            raise ValueError("Debtor no encontrado")
        history: List[Dict[str, str]] = []
        if context:
            history.append({"role": "system", "content": str(context)})
        debtor.conversation_history = history
        db.commit()
        return Conversation(conversation_id=str(debtor_id), history=history, state=debtor.state)
    finally:
        db.close()


def continue_conversation(conversation_id: str, message: str) -> ConversationUpdate:
    """Continúa una conversación existente, añade el mensaje, llama a IA y retorna la actualización."""
    db: Session = SessionLocal()
    try:
        phone: Optional[str] = None
        debtor: Optional[Debtor] = None
        if conversation_id.isdigit():
            debtor = db.query(Debtor).filter(Debtor.id == int(conversation_id)).first()
            if debtor and debtor.phone:
                phone = str(debtor.phone)
        else:
            phone = conversation_id
            debtor = db.query(Debtor).filter(Debtor.phone == phone).first()
        if not debtor or not phone:
            raise ValueError("Conversación no encontrada para conversation_id")

        import asyncio
        from services.conversation_service import handle_incoming_message
        response_text = asyncio.run(handle_incoming_message(phone, message, db))
        # Recargar historial y estado actualizado
        updated_debtor = db.query(Debtor).filter(Debtor.id == debtor.id).first()
        history = updated_debtor.conversation_history if updated_debtor else []
        state = updated_debtor.state if updated_debtor else None
        return ConversationUpdate(conversation_id=conversation_id, response=response_text, history=history, state=state)
    finally:
        db.close()


def classify_state(text: str) -> str:
    """Clasifica estado usando OpenAI a través del servicio unificado."""
    try:
        return openai_service.classify_state(text)
    except Exception:
        return "GRIS"
from models.Debtor import Debtor
from models.Campaign import Campaign
from models.DebtorDataset import DebtorDataset
from models.Strategy import Strategy
from services.debtor_service import update_state
from services.openai_service import generate_openai_response_sync
from services.whatsapp_service import send_whatsapp_message
from services.structured_prompt_service import structured_prompt_service
from services.traceability_service import traceability_service
from services.payment_link_service import payment_link_service
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
    debtor.state = cast(str, new_state)  # type: ignore

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

    # Check for payment link request using the new service
    current_custom_data = cast(Dict[str, Any], debtor.custom_data) if debtor.custom_data is not None else {}
    should_generate_link, reason, link_data = payment_link_service.should_generate_payment_link(
        user_message=body,
        debtor_state=new_state,
        conversation_history=current_history,
        debtor_data=current_custom_data
    )
    
    print(f"[DEBUG] Payment link analysis - Should generate: {should_generate_link}, Reason: {reason}")

    if should_generate_link:
        print("[DEBUG] Payment link should be generated. Creating response.")
        response_text = payment_link_service.generate_payment_link_response(
            debtor_state=new_state,
            debtor_data=current_custom_data,
            decision_data=link_data
        )
        
        # Si es estado VERDE, generar el link real
        if new_state == "VERDE":
            debt_amount = current_custom_data.get("deuda", 0)
            payment_info = payment_link_service.create_payment_link(
                debtor_id=cast(int, debtor.id),
                amount=float(debt_amount) if debt_amount else 0,
                method="mock"
            )
            # Reemplazar el placeholder con el link real
            response_text = response_text.replace("[GENERAR_LINK_AQUI]", payment_info["payment_link"])
        
        current_history.append({"role": "assistant", "content": response_text})
        debtor.conversation_history = cast(List[Dict[str, str]], current_history)  # type: ignore
        db.commit()
        print("[DEBUG] Payment link response generated. Returning.")
        return response_text

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
            debtor.conversation_history = cast(List[Dict[str, str]], current_history)  # type: ignore
            db.commit()
            # send_whatsapp_message(f"whatsapp:{phone}", response_text) # REMOVED
            print("[DEBUG] Direct debt response generated. Returning.")
            return response_text # Return the response text
        else:
            print("[DEBUG] Debt amount not a valid number or not found. Falling back to LLM.")

    # Get strategy information for LLM processing
    current_custom_data_for_llm = cast(Dict[str, Any], debtor.custom_data) if debtor.custom_data is not None else {}

    # Find active campaign and strategy
    active_campaign: Optional[Campaign] = None
    strategy: Optional[Strategy] = None
    
    if debtor.debtor_dataset and debtor.debtor_dataset.campaigns:
        for campaign_obj in debtor.debtor_dataset.campaigns:
            if campaign_obj.status == "active" and campaign_obj.strategy:
                active_campaign = campaign_obj
                strategy = campaign_obj.strategy
                break

    # Determine if this is the first message
    is_first_message = len(current_history) <= 2  # user message + assistant response

    if strategy:
        print(f"[DEBUG] Using strategy: {strategy.name}")
        
        # Generate structured prompt using the new rule decision system
        prompt_result = structured_prompt_service.generate_action_specific_prompt(
            strategy=strategy,
            debtor_data=current_custom_data_for_llm,
            current_state=new_state,
            conversation_history=current_history,
            user_message=body,
            is_first_message=is_first_message
        )
        
        structured_prompt = prompt_result['prompt']
        decision = prompt_result['decision']
        
        print(f"[DEBUG] Generated structured prompt length: {len(structured_prompt)}")
        print(f"[DEBUG] Action type: {decision.action_type}")
        print(f"[DEBUG] Structured prompt preview: {structured_prompt[:500]}...")
        
    else:
        print("[DEBUG] No active campaign or strategy found. Using default prompt.")
        structured_prompt = """
Actuás como un asistente especializado en cobranzas.
Tu misión es contactar de manera eficiente a un deudor para facilitar el pago.
No respondas como humano ni toques temas irrelevantes.

INFORMACIÓN DEL DEUDOR:
- Estado actual: GRIS

INSTRUCCIONES ESPECÍFICAS: Usar tono profesional y respetuoso para establecer comunicación.

INSTRUCCIONES FINALES:
- Responde de manera profesional y empática
- Mantén el enfoque en la cobranza
- NO inventes descuentos, cuotas o condiciones no autorizadas
"""

    # Convert conversation history to OpenAI format
    messages: List[ChatCompletionMessageParam] = []
    
    # Add system message with structured prompt
    messages.append(ChatCompletionSystemMessageParam(role="system", content=structured_prompt))
    
    # Add conversation history (excluding system messages)
    for msg in current_history:
        if msg['role'] == 'user':
            messages.append(ChatCompletionUserMessageParam(role="user", content=msg['content']))
        elif msg['role'] == 'assistant':
            messages.append(ChatCompletionAssistantMessageParam(role="assistant", content=msg['content']))

    # Generate response using OpenAI
    response = generate_openai_response_sync(messages=messages)

    current_history.append({"role": "assistant", "content": response})
    debtor.conversation_history = cast(List[Dict[str, str]], current_history)  # type: ignore
    db.commit()

    # Log decision for traceability
    if strategy:
        traceability_service.log_rule_decision(
            debtor_id=cast(int, debtor.id),
            strategy_id=cast(int, strategy.id),
            user_message=body,
            decision=decision,
            llm_response=response,
            conversation_history=current_history,
            debtor_data=current_custom_data_for_llm
        )

    # send_whatsapp_message(f"whatsapp:{phone}", response) # REMOVED
    print("[DEBUG] LLM response generated. Returning.")
    return response # Return the response text
