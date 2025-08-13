from openai import OpenAI
import json
from typing import List, Dict, Any, Optional, Union
from openai.types.chat import ChatCompletionMessageParam, ChatCompletionSystemMessageParam, ChatCompletionUserMessageParam

from services.cache_service import RedisCache
from core.metrics import cache_hit_counter, cache_miss_counter
import hashlib
from tasks.openai_tasks import celery_app
import os
from dotenv import load_dotenv
import structlog
# Importar tareas Celery para OpenAI
from tasks.openai_tasks import (
    generate_first_message_task,
    generate_response_task, 
    classify_state_task,
    analyze_conversation_context_task
)

logger = structlog.get_logger()

load_dotenv()

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

VALID_STATES = {"VERDE", "AMARILLO", "ROJO", "GRIS"}



async def get_cached_ia_response(prompt, params):
    cache = await RedisCache.get_instance()
    key_raw = json.dumps({"prompt": prompt, "params": params}, sort_keys=True)
    cache_key = "ia_response:" + hashlib.sha256(key_raw.encode()).hexdigest()
    cached = await cache.get(cache_key)
    if cached:
        cache_hit_counter.inc()
        return json.loads(cached)
    cache_miss_counter.inc()
    # ... lógica original para obtener respuesta IA ...
    response = ... # resultado de la IA
    await cache.set(cache_key, json.dumps(response), ttl=600)
    return response


def analyze_conversation_context(conversation_history: Optional[List[Dict[str, str]]], current_message: str) -> Dict[str, Any]:
    """
    Analiza el contexto de la conversación para detectar patrones importantes.
    """
    analysis = {
        "has_payment_intent": False,
        "has_identity_confirmation": False,
        "has_positive_response": False,
        "has_negotiation": False,
        "has_rejection": False,
        "is_cooperative": False,
        "context_indicators": []
    }
    
    # Permitir analizar aunque no haya historial, siempre analizar el mensaje actual
    user_messages = []
    if conversation_history:
        user_messages = [msg['content'].lower() for msg in conversation_history if msg.get('role') == 'user']
    user_messages.append(current_message.lower())
    
    # Detectar intención de pago (mejorado)
    payment_keywords = [
        'quiero pagar', 'pagar', 'acepto', 'ok', 'bueno', 'sí', 'si', 'dame el link', 
        'link de pago', 'quiero', 'acepto pagar', 'puedo pagar', 'me interesa pagar',
        'quiero el link', 'dame el link', 'envíame el link', 'quiero pagar ahora'
    ]
    
    # Detectar confirmación de identidad (mejorado para incluir DNI)
    identity_keywords = [
        'dni', 'documento', 'mi dni es', 'mi documento es', 'soy', 'mi nombre es',
        'mi dni', 'mi documento', 'documento nacional', 'identidad'
    ]
    
    # Detectar respuestas positivas (mejorado, incluye 'si' sin tilde y variantes)
    positive_keywords = ['sí', 'si', 'ok', 'bueno', 'acepto', 'quiero', 'claro', 'perfecto', 'dale', 'si ', ' si', 'si.']
    
    # Detectar negociación
    negotiation_keywords = ['descuento', 'cuotas', 'plazos', 'tiempo', 'pensar', 'ver', 'cuánto', 'precio']
    
    # Detectar rechazo (mejorado para evitar conflictos con palabras de pago)
    rejection_keywords = ['no puedo', 'no tengo', 'no quiero', 'imposible', 'déjenme en paz', 'no', 'no gracias', 'no voy a pagar', 'no pago']
    
    # Analizar cada mensaje
    for msg in user_messages:
        msg_stripped = msg.strip().lower()
        
        # Detectar rechazo PRIMERO (prioridad sobre intención de pago)
        has_rejection = any(keyword in msg for keyword in rejection_keywords)
        if has_rejection:
            analysis["has_rejection"] = True
            analysis["context_indicators"].append("rechazo")
            # Si hay rechazo, NO marcar intención de pago ni respuesta positiva
            continue
        
        # Detectar confirmación de identidad (incluyendo números de DNI)
        # Si el mensaje es solo números (DNI), considerarlo confirmación de identidad
        if msg_stripped.isdigit() and len(msg_stripped) >= 7:  # DNI típico argentino
            analysis["has_identity_confirmation"] = True
            analysis["context_indicators"].append("confirmación_identidad")
            # Si confirma identidad, también marcar como cooperativo
            analysis["is_cooperative"] = True
            continue
        
        # Detectar intención de pago (solo si NO hay rechazo)
        if any(keyword in msg for keyword in payment_keywords):
            analysis["has_payment_intent"] = True
            analysis["context_indicators"].append("intención_de_pago")
        
        # Detectar confirmación de identidad
        if any(keyword in msg for keyword in identity_keywords):
            analysis["has_identity_confirmation"] = True
            analysis["context_indicators"].append("confirmación_identidad")
        
        # Detectar respuestas positivas (solo si NO hay rechazo)
        # Considerar 'si' y 'sí' como palabra exacta (sin espacios, sin importar mayúsculas)
        if any(
            kw in msg for kw in positive_keywords
        ) or msg_stripped in ['si', 'sí']:
            analysis["has_positive_response"] = True
            analysis["context_indicators"].append("respuesta_positiva")
        
        # Detectar negociación
        if any(keyword in msg for keyword in negotiation_keywords):
            analysis["has_negotiation"] = True
            analysis["context_indicators"].append("negociación")
    
    # Detectar contexto de pago en curso
    payment_context_keywords = ['link', 'pago', 'pagar', 'deuda', 'cuenta', 'regularizar']
    has_payment_context = any(
        any(keyword in msg for keyword in payment_context_keywords)
        for msg in user_messages
    )
    
    if has_payment_context:
        analysis["context_indicators"].append("contexto_de_pago")
    
    # Ajuste: Si el último mensaje tiene intención de pago o respuesta positiva (y no hay rechazo), marcar como cooperativo
    last_msg = user_messages[-1]
    last_msg_stripped = last_msg.strip().lower()
    last_has_rejection = any(keyword in last_msg for keyword in rejection_keywords)
    
    if not last_has_rejection:
        # Si el último mensaje es un DNI, ya está marcado como cooperativo arriba
        if not (last_msg_stripped.isdigit() and len(last_msg_stripped) >= 7):
            last_has_payment_intent = any(keyword in last_msg for keyword in payment_keywords)
            last_has_positive_response = any(keyword in last_msg for keyword in positive_keywords) or last_msg_stripped in ['si', 'sí']
            
            if (last_has_payment_intent or last_has_positive_response):
                analysis["is_cooperative"] = True
            elif (analysis["has_payment_intent"] or analysis["has_positive_response"]) and not analysis["has_rejection"]:
                analysis["is_cooperative"] = True
    
    return analysis


def generate_openai_first_message_sync(initial_instruction: str, model: str = "gpt-4o-mini") -> str:
    """
    Genera el mensaje inicial usando el prompt estructurado.
    
    Args:
        initial_instruction: El prompt específico de la estrategia
        model: Modelo de OpenAI a usar
    
    Returns:
        El mensaje inicial generado
    """
    system_prompt = f"""
Actuás como un asistente especializado en cobranzas.
Tu misión es contactar de manera eficiente a un deudor para facilitar el pago.
No respondas como humano ni toques temas irrelevantes.

PROMPT INICIAL: {initial_instruction}

Genera un mensaje inicial apropiado basado en estas instrucciones.
"""
    
    messages: List[ChatCompletionMessageParam] = [
        ChatCompletionSystemMessageParam(role="system", content=system_prompt),
        ChatCompletionUserMessageParam(role="user", content="Genera el mensaje inicial para el deudor."),
    ]
    response = openai_client.chat.completions.create(
        model=model,
        messages=messages,
    )
    content = response.choices[0].message.content
    if content is None:
        raise ValueError("OpenAI response content was None for initial message.")
    return content


def generate_openai_response_sync(
    messages: List[ChatCompletionMessageParam], 
    model: str = "gpt-4o-mini"
) -> str:
    """
    Genera una respuesta usando el sistema de prompts estructurados.
    
    Args:
        messages: Lista de mensajes incluyendo el system message con prompt estructurado
        model: Modelo de OpenAI a usar
    
    Returns:
        La respuesta generada
    """
    response = openai_client.chat.completions.create(
        model=model,
        messages=messages,
    )
    content = response.choices[0].message.content
    if content is None:
        raise ValueError("OpenAI response content was None for general response.")
    return content


def classify_state(message: str, conversation_history: Optional[List[Dict[str, str]]] = None) -> str:
    # Construir el contexto completo de la conversación
    if conversation_history:
        full_conversation = "\n".join([
            f"{msg.get('role', 'user')}: {msg.get('content', '')}"
            for msg in conversation_history
        ])
        full_conversation += f"\nuser: {message}"
    else:
        full_conversation = f"user: {message}"
    
    # Analizar el contexto completo para detectar patrones
    context_analysis = analyze_conversation_context(conversation_history, message)
    
    prompt = f"""
Sos un agente experto en cobranzas. Analizá esta conversación y clasificá la intención de pago del deudor como uno de los siguientes estados:

ESTADOS Y SUS CARACTERÍSTICAS:

🟢 VERDE (Disposición Positiva):
- Dice "sí", "ok", "bueno", "acepto", "quiero pagar"
- Solicita el link de pago directamente
- Confirma datos de identidad (DNI, email)
- Muestra disposición inmediata a pagar
- Dice "cuando puedo pagar", "dónde pago", "cómo pago"
- Responde positivamente a ofertas de pago
- Confirma que quiere el link de pago

🟡 AMARILLO (Interés con Negociación):
- Muestra interés pero pide descuentos
- Dice "cuánto descuento hay", "puedo pagar en cuotas"
- Pide más tiempo: "el mes que viene", "en unos días"
- Negocia condiciones: "y si pago la mitad", "puedo pagar menos"
- Dice "tengo que ver", "déjame pensar", "hablo con mi familia"
- Solicita información adicional antes de decidir

🔴 ROJO (Rechazo o Evasión):
- Dice "no puedo", "no tengo dinero", "no quiero"
- Se enoja o es agresivo: "déjenme en paz", "no me molesten"
- Niega la deuda: "eso no es mío", "no reconozco esa deuda"
- Evita el tema: "después hablamos", "no tengo tiempo"
- Dice "imposible", "no voy a pagar", "corten la línea"
- Bloquea o ignora los mensajes

⚪ GRIS (Sin Información Suficiente o No es la Persona):
- El usuario NO responde (conversación vacía o solo saludos genéricos como "hola", "buenos días")
- El usuario dice explícitamente que NO es la persona buscada ("no soy", "número equivocado", "no corresponde", "no es mi deuda", "no conozco a esa persona")

⚠️ IMPORTANTE: SOLO devuelvas GRIS si se cumple estrictamente uno de estos dos casos:
1. El usuario no responde o solo saluda sin dar información relevante.
2. El usuario niega explícitamente ser la persona buscada.

En cualquier otro caso (aunque la respuesta sea corta, ambigua o de duda), si hay palabras relacionadas con pago, negociación, rechazo, o cualquier interacción relevante, el estado debe ser VERDE, AMARILLO o ROJO según corresponda.

ANÁLISIS DE CONTEXTO DETECTADO:
- Intención de pago: {'SÍ' if context_analysis['has_payment_intent'] else 'NO'}
- Confirmación de identidad: {'SÍ' if context_analysis['has_identity_confirmation'] else 'NO'}
- Respuesta positiva: {'SÍ' if context_analysis['has_positive_response'] else 'NO'}
- Negociación: {'SÍ' if context_analysis['has_negotiation'] else 'NO'}
- Rechazo: {'SÍ' if context_analysis['has_rejection'] else 'NO'}
- Cooperativo: {'SÍ' if context_analysis['is_cooperative'] else 'NO'}
- Indicadores: {', '.join(context_analysis['context_indicators']) if context_analysis['context_indicators'] else 'Ninguno'}

CONVERSACIÓN COMPLETA:
{full_conversation}

REGLAS DE CLASIFICACIÓN ESTRICTAS:
- SOLO devuelvas GRIS si el usuario no responde o niega ser la persona buscada.
- Si hay cualquier palabra de pago, negociación, rechazo, o interacción relevante, NUNCA devuelvas GRIS.
- Si la respuesta es corta pero hay contexto de pago, NO devuelvas GRIS.

Devolvé solo una palabra exacta en mayúsculas: VERDE, AMARILLO, ROJO o GRIS.
"""

    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[ChatCompletionUserMessageParam(role="user", content=prompt)],
            temperature=0
        )

        state_content = response.choices[0].message.content
        if state_content is None:
            raise ValueError("OpenAI response content was None for state classification.")

        state = state_content.strip().upper()

        if state not in VALID_STATES:
            logger.warning(f"Estado inválido devuelto por GPT: {state}, usando GRIS como fallback")
            return "GRIS"

        return state
    except Exception as e:
        logger.error(f"Error en classify_state: {e}, usando GRIS como fallback")
        return "GRIS"


# ============================================================================
# WRAPPERS ASÍNCRONOS PARA CELERY
# ============================================================================
# Estas funciones encolan las tareas en Celery y devuelven task_id para seguimiento
# Las funciones síncronas originales se mantienen para compatibilidad y testing

def generate_first_message_async(initial_instruction: str, model: str = "gpt-4o-mini") -> str:
    """
    Wrapper asíncrono que encola la generación del primer mensaje en Celery.
    
    Args:
        initial_instruction: Instrucción inicial para el bot
        model: Modelo de OpenAI a usar
        
    Returns:
        str: Task ID de Celery para seguimiento
        
    Note:
        Para obtener el resultado, usar: task = generate_first_message_task.AsyncResult(task_id)
        task.get() para esperar el resultado, o task.ready() para verificar si está listo
    """
    task = generate_first_message_task.delay(initial_instruction, model)
    return task.id

def generate_response_async(messages: List[ChatCompletionMessageParam], model: str = "gpt-4o-mini") -> str:
    """
    Wrapper asíncrono que encola la generación de respuesta en Celery.
    
    Args:
        messages: Lista de mensajes de la conversación
        model: Modelo de OpenAI a usar
        
    Returns:
        str: Task ID de Celery para seguimiento
        
    Note:
        Para obtener el resultado, usar: task = generate_response_task.AsyncResult(task_id)
        task.get() para esperar el resultado, o task.ready() para verificar si está listo
    """
    task = generate_response_task.delay(messages, model)
    return task.id

def classify_state_async(message: str, conversation_history: Optional[List[Dict[str, str]]] = None) -> str:
    """
    Wrapper asíncrono que encola la clasificación de estado en Celery.
    
    Args:
        message: Mensaje actual del usuario
        conversation_history: Historial de la conversación
        
    Returns:
        str: Task ID de Celery para seguimiento
        
    Note:
        Para obtener el resultado, usar: task = classify_state_task.AsyncResult(task_id)
        task.get() para esperar el resultado, o task.ready() para verificar si está listo
    """
    task = classify_state_task.delay(message, conversation_history)
    return task.id

def analyze_conversation_context_async(conversation_history: List[Dict[str, str]], current_message: str) -> str:
    """
    Wrapper asíncrono que encola el análisis de contexto en Celery.
    
    Args:
        conversation_history: Historial de la conversación
        current_message: Mensaje actual del usuario
        
    Returns:
        str: Task ID de Celery para seguimiento
        
    Note:
        Para obtener el resultado, usar: task = analyze_conversation_context_task.AsyncResult(task_id)
        task.get() para esperar el resultado, o task.ready() para verificar si está listo
    """
    task = analyze_conversation_context_task.delay(conversation_history, current_message)
    return task.id

def get_task_result(task_id: str, timeout: int = 30) -> Union[str, Dict[str, Any], None]:
    """
    Obtiene el resultado de una tarea Celery por su ID.
    
    Args:
        task_id: ID de la tarea Celery
        timeout: Tiempo máximo de espera en segundos
        
    Returns:
        Union[str, Dict[str, Any], None]: Resultado de la tarea o None si hay timeout/error
        
    Note:
        Esta función es útil para obtener resultados de tareas asíncronas
        cuando se necesita el resultado inmediatamente en el hilo principal
    """
    try:
        task = celery_app.AsyncResult(task_id)
        return task.get(timeout=timeout)
    except Exception as e:
        logger.error(f"Error obteniendo resultado de tarea {task_id}: {e}")
        return None
