from openai import OpenAI

openai_client = OpenAI(api_key="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")

VALID_STATES = {"VERDE", "AMARILLO", "ROJO", "GRIS"}



def generate_openai_first_message_sync(prompt: str, model: str = "gpt-4o-mini") -> str:
    response = openai_client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content


def generate_openai_response_sync(messages: list, model: str = "gpt-4o-mini") -> str:
    response = openai_client.chat.completions.create(
        model=model,
        messages=messages,
    )
    return response.choices[0].message.content



def classify_state(message):
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
    messages=[{"role": "user", "content": prompt}],
    temperature=0
    )

    state = response.choices[0].message.content.strip().upper()


    if state not in VALID_STATES:
        raise ValueError(f"Estado inválido devuelto por GPT: {state}")

    return state
