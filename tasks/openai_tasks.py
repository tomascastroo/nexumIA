"""
Tareas Celery para OpenAI con reintentos automáticos y manejo de errores.
Todas las llamadas a OpenAI se procesan de forma asíncrona para evitar bloqueos en el hilo principal.
"""
from .celery_app import celery_app
import structlog
from openai import OpenAI
import os
from typing import List, Dict, Any, Optional
from openai.types.chat import ChatCompletionMessageParam
from dotenv import load_dotenv
import json

load_dotenv()

logger = structlog.get_logger()
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

VALID_STATES = {"VERDE", "AMARILLO", "ROJO", "GRIS"}

@celery_app.task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def generate_first_message_task(self, initial_instruction: str, model: str = "gpt-4o-mini") -> str:
    """
    Genera el primer mensaje de la conversación usando OpenAI.
    
    Args:
        initial_instruction: Instrucción inicial para el bot
        model: Modelo de OpenAI a usar
        
    Returns:
        str: Mensaje generado por IA
        
    Raises:
        Exception: Se reintenta automáticamente hasta 3 veces con backoff exponencial
    """
    try:
        logger.info("Generando primer mensaje con OpenAI", 
                   instruction=initial_instruction, model=model, task_id=self.request.id)
        
        messages = [
            {"role": "system", "content": initial_instruction},
            {"role": "user", "content": "Genera un mensaje inicial amigable y profesional para iniciar una conversación de cobranza."}
        ]
        
        response = openai_client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=150,
            temperature=0.7
        )
        
        message = response.choices[0].message.content
        logger.info("Primer mensaje generado exitosamente", task_id=self.request.id)
        return message
        
    except Exception as e:
        logger.error("Error generando primer mensaje", 
                    error=str(e), task_id=self.request.id, retry_count=self.request.retries)
        raise  # Celery reintentará automáticamente

@celery_app.task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def generate_response_task(self, messages: List[ChatCompletionMessageParam], model: str = "gpt-4o-mini") -> str:
    """
    Genera una respuesta a la conversación usando OpenAI.
    
    Args:
        messages: Lista de mensajes de la conversación
        model: Modelo de OpenAI a usar
        
    Returns:
        str: Respuesta generada por IA
        
    Raises:
        Exception: Se reintenta automáticamente hasta 3 veces con backoff exponencial
    """
    try:
        logger.info("Generando respuesta con OpenAI", 
                   message_count=len(messages), model=model, task_id=self.request.id)
        
        response = openai_client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=200,
            temperature=0.7
        )
        
        message = response.choices[0].message.content
        logger.info("Respuesta generada exitosamente", task_id=self.request.id)
        return message
        
    except Exception as e:
        logger.error("Error generando respuesta", 
                    error=str(e), task_id=self.request.id, retry_count=self.request.retries)
        raise  # Celery reintentará automáticamente

@celery_app.task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def classify_state_task(self, message: str, conversation_history: Optional[List[Dict[str, str]]] = None) -> str:
    """
    Clasifica el estado del deudor usando OpenAI.
    
    Args:
        message: Mensaje actual del usuario
        conversation_history: Historial de la conversación
        
    Returns:
        str: Estado clasificado (VERDE, AMARILLO, ROJO, GRIS)
        
    Raises:
        Exception: Se reintenta automáticamente hasta 3 veces con backoff exponencial
    """
    try:
        logger.info("Clasificando estado con OpenAI", 
                   message_length=len(message), has_history=bool(conversation_history), task_id=self.request.id)
        
        # Construir el contexto completo de la conversación
        system_prompt = """Eres un experto en análisis de comportamiento y clasificación de deudores. 
        Tu tarea es clasificar el estado del deudor basándote en su mensaje y el historial de conversación.
        
        Estados posibles:
        - VERDE: Deudor muy cooperativo, quiere pagar, confirma identidad, pide link de pago
        - AMARILLO: Deudor cooperativo pero con dudas, pide información, negocia
        - ROJO: Deudor poco cooperativo, evasivo, no responde claramente
        - GRIS: Deudor neutral, no hay indicadores claros, primera interacción
        
        Responde SOLO con el estado (VERDE, AMARILLO, ROJO o GRIS), sin explicaciones adicionales."""
        
        # Construir mensajes para OpenAI
        openai_messages = [{"role": "system", "content": system_prompt}]
        
        # Agregar historial de conversación si existe
        if conversation_history:
            for msg in conversation_history[-5:]:  # Últimos 5 mensajes para contexto
                role = "user" if msg.get("role") == "user" else "assistant"
                openai_messages.append({"role": role, "content": msg.get("content", "")})
        
        # Agregar mensaje actual
        openai_messages.append({"role": "user", "content": message})
        
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=openai_messages,
            max_tokens=10,
            temperature=0.1  # Baja temperatura para respuestas consistentes
        )
        
        state = response.choices[0].message.content.strip().upper()
        
        # Validar que el estado sea válido
        if state not in VALID_STATES:
            logger.warning("Estado inválido recibido de OpenAI, usando GRIS por defecto", 
                          received_state=state, task_id=self.request.id)
            state = "GRIS"
        
        logger.info("Estado clasificado exitosamente", 
                   state=state, task_id=self.request.id)
        return state
        
    except Exception as e:
        logger.error("Error clasificando estado", 
                    error=str(e), task_id=self.request.id, retry_count=self.request.retries)
        raise  # Celery reintentará automáticamente

@celery_app.task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def analyze_conversation_context_task(self, conversation_history: List[Dict[str, str]], current_message: str) -> Dict[str, Any]:
    """
    Analiza el contexto de la conversación usando OpenAI para detectar patrones importantes.
    
    Args:
        conversation_history: Historial de la conversación
        current_message: Mensaje actual del usuario
        
    Returns:
        Dict: Análisis del contexto con indicadores clave
        
    Raises:
        Exception: Se reintenta automáticamente hasta 3 veces con backoff exponencial
    """
    try:
        logger.info("Analizando contexto de conversación con OpenAI", 
                   history_length=len(conversation_history), task_id=self.request.id)
        
        system_prompt = """Analiza el contexto de esta conversación de cobranza y detecta patrones importantes.
        
        Responde con un JSON que contenga:
        {
            "has_payment_intent": boolean,
            "has_identity_confirmation": boolean,
            "has_positive_response": boolean,
            "has_negotiation": boolean,
            "has_rejection": boolean,
            "is_cooperative": boolean,
            "context_indicators": [string],
            "confidence_score": float (0.0-1.0)
        }
        
        Solo responde con el JSON, sin texto adicional."""
        
        # Construir mensajes para OpenAI
        openai_messages = [{"role": "system", "content": system_prompt}]
        
        # Agregar historial de conversación
        for msg in conversation_history[-10:]:  # Últimos 10 mensajes
            role = "user" if msg.get("role") == "user" else "assistant"
            openai_messages.append({"role": role, "content": msg.get("content", "")})
        
        # Agregar mensaje actual
        openai_messages.append({"role": "user", "content": current_message})
        
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=openai_messages,
            max_tokens=200,
            temperature=0.1
        )
        
        try:
            analysis = json.loads(response.choices[0].message.content)
            logger.info("Contexto analizado exitosamente", 
                       analysis=analysis, task_id=self.request.id)
            return analysis
        except json.JSONDecodeError:
            logger.warning("Respuesta de OpenAI no es JSON válido, usando análisis por defecto", 
                          response=response.choices[0].message.content, task_id=self.request.id)
            # Fallback a análisis básico
            return {
                "has_payment_intent": False,
                "has_identity_confirmation": False,
                "has_positive_response": False,
                "has_negotiation": False,
                "has_rejection": False,
                "is_cooperative": False,
                "context_indicators": ["fallback_analysis"],
                "confidence_score": 0.5
            }
        
    except Exception as e:
        logger.error("Error analizando contexto de conversación", 
                    error=str(e), task_id=self.request.id, retry_count=self.request.retries)
        raise  # Celery reintentará automáticamente 