from sqlalchemy.orm import Session, joinedload
from datetime import date, timedelta, datetime
from models.Debtor import Debtor
from models.Strategy import Strategy
from models.Campaign import Campaign
from models.DebtorDataset import DebtorDataset
import structlog

logger = structlog.get_logger()
# Import removed - handle_incoming_message was refactored out
# For automated follow-up messages, use the new conversation service or WhatsApp service directly

def run_daily_followups(db: Session):
    """
    This function will be run daily to check for debtors needing follow-up.
    """
    today = date.today()

    # Get debtors that need follow-up today
    debtors_for_followup = db.query(Debtor).options(
        joinedload(Debtor.debtor_dataset).joinedload(DebtorDataset.campaigns).joinedload(Campaign.strategy)
    ).filter(
        Debtor.proximo_contacto <= today
    ).all()

    for debtor in debtors_for_followup:
        if not debtor.debtor_dataset or not debtor.debtor_dataset.campaigns:
            logger.debug(f"Skipping debtor {debtor.id}: No associated debtor dataset or campaigns.")
            continue

        active_campaign = None
        for campaign in debtor.debtor_dataset.campaigns:
            # Assuming a campaign is active if its status is 'active' and it's within its date range
            if campaign.status == "active" and (campaign.start_date.date() <= today) and (campaign.end_date is None or campaign.end_date.date() >= today):
                active_campaign = campaign
                break

        if not active_campaign or not active_campaign.strategy:
            logger.debug(f"Skipping debtor {debtor.id}: No active campaign or strategy found.")
            continue

        strategy = active_campaign.strategy
        rules = strategy.reglas_frecuencia_contacto or []
        debtor_data = {
            "edad": debtor.custom_data.get("edad"),
            "sexo": debtor.custom_data.get("sexo"),
            "monto_deuda": debtor.custom_data.get("monto_deuda"),
            "estado": debtor.state,
            # ...otros campos relevantes
        }
        days_to_add = get_frecuencia_from_rules(rules, debtor_data)

        if days_to_add > 0:
            next_contact_date = today + timedelta(days=days_to_add)
            
            # Send message (you might need to adapt this based on handle_incoming_message's signature)
            # For now, this is a placeholder. You'll likely need to pass appropriate message_body and profile_id.
            logger.info(f"Sending follow-up message to debtor {debtor.id} (phone: {debtor.phone}) with state {debtor.state}.")
            # Assuming handle_incoming_message can be called to initiate a message from the bot side
            # This part needs careful review and potential adaptation
            # For a bot-initiated message, you might need a different service function than handle_incoming_message
            # which is typically for incoming user messages.
# Conversación unificada: usar services.conversation_service si se requiere enviar mensajes automatizados
            
            # Placeholder for actual message sending logic
            # handle_incoming_message(db, "whatsapp", "follow_up_message", debtor.phone, "auto_followup_profile_id") 
            
            debtor.ultimo_contacto = datetime.utcnow()
            debtor.proximo_contacto = datetime.combine(next_contact_date, datetime.min.time())
            db.add(debtor)
            db.commit()
            db.refresh(debtor)
            logger.info(f"Debtor {debtor.id} next contact scheduled for {next_contact_date}.")
        else:
            logger.debug(f"Debtor {debtor.id} with state {debtor.state} has 0 days configured for follow-up.")

    db.close() 