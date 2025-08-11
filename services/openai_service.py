from openai import OpenAI
import json
from typing import List, Dict, Any, Optional
from openai.types.chat import ChatCompletionMessageParam, ChatCompletionSystemMessageParam, ChatCompletionUserMessageParam, ChatCompletionAssistantMessageParam

openai_client = OpenAI(api_key="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")

VALID_STATES = {"VERDE", "AMARILLO", "ROJO", "GRIS"}


def generate_openai_first_message_sync(initial_instruction: str, model: str = "gpt-4o-mini") -> str:
    messages: List[ChatCompletionMessageParam] = [
        ChatCompletionSystemMessageParam(role="system", content="You are a professional debt collection agent. Generate an initial message for a debtor based on the following instructions."),
        ChatCompletionUserMessageParam(role="user", content=initial_instruction),
    ]
    response = openai_client.chat.completions.create(
        model=model,
        messages=messages,
    )
    content = response.choices[0].message.content
    if content is None:
        raise ValueError("OpenAI response content was None for initial message.")
    return content


def generate_openai_response_sync(messages: List[ChatCompletionMessageParam], model: str = "gpt-4o-mini") -> str:
    response = openai_client.chat.completions.create(
        model=model,
        messages=messages,
    )
    content = response.choices[0].message.content
    if content is None:
        raise ValueError("OpenAI response content was None for general response.")
    return content


def classify_state(message: str) -> str:
    prompt = f"""
Sos un agente experto en cobranzas. Analizá esta conversación y clasificá la intención de pago del deudor como uno de los siguientes estados:

- VERDE: está decidido a pagar pronto.
- AMARILLO: muestra interés pero pide negociar o demora.
- ROJO: niega, evita o rechaza.
- GRIS: aún no respondió o no hay info suficiente.

Conversación:
{message}

Devolvé solo una palabra exacta en mayúsculas: VERDE, AMARILLO, ROJO o GRIS.
"""

    response = openai_client.chat.completions.create(
        model="gpt-4",
        messages=[ChatCompletionUserMessageParam(role="user", content=prompt)],
        temperature=0
    )

    state_content = response.choices[0].message.content
    if state_content is None:
        raise ValueError("OpenAI response content was None for state classification.")

    state = state_content.strip().upper()

    if state not in VALID_STATES:
        raise ValueError(f"Estado inválido devuelto por GPT: {state}")

    return state
