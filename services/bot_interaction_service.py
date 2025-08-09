from services.conversation_service import continue_conversation

async def handle_incoming_message(bot_id: int, user_phone: str, message_text: str):
    # Fachada delgada: delega en conversation_service unificado
    update = continue_conversation(user_phone, message_text)
    return update.get("response", "")
