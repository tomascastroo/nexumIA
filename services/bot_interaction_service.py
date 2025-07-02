from services import bot_service, openai_service, whatsapp_service

async def handle_incoming_message(bot_id: int, user_phone: str, message_text: str):
    # 1. Obtené el bot (con sus estrategias) desde DB
    bot = bot_service.get_bot(bot_id)
    if not bot:
        raise Exception("Bot no encontrado")

    # 2. Construí prompt para OpenAI (podés usar info de la campaña/estrategia del bot)
    prompt = f"Usuario dice: {message_text}\nResponde según estrategia del bot {bot.name}"

    # 3. Llamá a OpenAI para obtener respuesta
    reply_text = await openai_service.generate_openai_response(prompt)

    # 4. Enviar respuesta por WhatsApp
    await whatsapp_service.send_whatsapp_message(user_phone, reply_text)

    # 5. Opcional: Guardar log, actualizar estado, etc.
    return reply_text
