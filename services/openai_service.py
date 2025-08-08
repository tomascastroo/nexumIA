import os
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables from .env file if present
load_dotenv()

# Create OpenAI client using API key from environment
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

VALID_STATES = {"VERDE", "AMARILLO", "ROJO", "GRIS"}

def generate_openai_first_message_sync(prompt: str, model: str = "gpt-4o-mini") -> str:
    response = openai_client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=400,
        temperature=0.7,
    )
    return response.choices[0].message.content

def generate_openai_response_sync(messages: list, model: str = "gpt-4o-mini") -> str:
    response = openai_client.chat.completions.create(
        model=model,
        messages=messages,
        max_tokens=400,
        temperature=0.7,
    )
    return response.choices[0].message.content

def classify_state(message: str) -> str:
    """
    Classify the debtor's payment intention into one of the valid states.
    """
    prompt = f"""Sos un agente experto en cobranzas. Analizá esta conversación y clasifica la intención de pago del deudor como uno de los siguientes estados:
- VERDE: está decidido a pagar pronto.
- AMARILLO: muestra interés pero pide negociar o demora.
- ROJO: niega, evita o rechaza.
- GRIS: aún no respondió o no hay info suficiente.

Conversación:
{message}

Respuesta (solo una palabra en mayúsculas de la lista anterior):"""
    response = generate_openai_response_sync([
        {"role": "user", "content": prompt}
    ], model="gpt-4o-mini")
    result = response.strip().upper()
    return result if result in VALID_STATES else "GRIS"
