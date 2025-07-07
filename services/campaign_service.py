import json
from pytest import Session
from models.Bot import Bot
from models.Debtor import Debtor
from models.Strategy import Strategy
from models.Campaign import Campaign
from db.db import SessionLocal
from models.DebtorDataset import DebtorDataset

from services.whatsapp_service import send_whatsapp_message
from services.openai_service import generate_openai_first_message_sync
from schemas.campaign import CampaignCreate,CampaignUpdate,CampaignRead
from fastapi import HTTPException
import re
import difflib

def create_campaign(db: Session, campaign: CampaignCreate, user_id: int):
    strategy = db.query(Strategy).filter(Strategy.id == campaign.strategy_id, Strategy.user_id == user_id).first()
    if not strategy:
        raise HTTPException(status_code=400, detail="Invalid strategy")

    bot = db.query(Bot).filter(Bot.id == campaign.bot_id, Bot.user_id == user_id).first()
    if not bot:
        raise HTTPException(status_code=400, detail="Invalid bot")

    dataset = db.query(DebtorDataset).filter(DebtorDataset.id == campaign.debtor_dataset_id, DebtorDataset.user_id == user_id).first()
    if not dataset:
        raise HTTPException(status_code=400, detail="Invalid debtor dataset")

    db_campaign = Campaign(
        name=campaign.name,
        bot_id=campaign.bot_id,
        strategy_id=campaign.strategy_id,
        debtor_dataset_id=campaign.debtor_dataset_id,
        status=campaign.status,
        start_date=campaign.start_date,
        end_date=campaign.end_date,
        user_id=user_id
    )
    db.add(db_campaign)
    db.commit()
    db.refresh(db_campaign)
    return db_campaign


def get_campaign(db: Session, campaign_id: int, user_id: int):
    return db.query(Campaign).filter(Campaign.id == campaign_id, Campaign.user_id == user_id).first()


def get_campaigns(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    return db.query(Campaign).filter(Campaign.user_id == user_id).offset(skip).limit(limit).all()


def update_campaign(db: Session, campaign_id: int, campaign_data: CampaignUpdate, user_id: int):
    db_campaign = get_campaign(db, campaign_id, user_id)
    if not db_campaign:
        return None

    for var, value in vars(campaign_data).items():
        if value is not None:
            setattr(db_campaign, var, value)
    db.commit()
    db.refresh(db_campaign)
    return db_campaign


def delete_campaign(db: Session, campaign_id: int, user_id: int):
    db_campaign = get_campaign(db, campaign_id, user_id)
    if not db_campaign:
        return None
    db.delete(db_campaign)
    db.commit()
    return db_campaign


def personalize_message(template: str, debtor: object) -> str:
    fields = re.findall(r"\[([^\]]+)\]", template)
    debtor_attrs = dir(debtor)
    message = template

    for field in fields:
        # Pasar a minúsculas y reemplazar espacios por guiones bajos para buscar atributo
        attr_name = field.lower().replace(" ", "_")
        
        if attr_name in debtor_attrs:
            value = getattr(debtor, attr_name)
        else:
            # Intentar encontrar atributo parecido con difflib
            matches = difflib.get_close_matches(attr_name, debtor_attrs, n=1, cutoff=0.6)
            if matches:
                value = getattr(debtor, matches[0])
            else:
                value = f"[{field}]"  # No se encontró, dejamos el placeholder
                
        message = message.replace(f"[{field}]", str(value))
    
    return message









def throw_campaign(db: Session, campaign_id: int, user_id: int):
    campaign = get_campaign(db, campaign_id, user_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    initial_prompt = campaign.strategy.initial_prompt
    message = generate_openai_first_message_sync(initial_prompt, "gpt-4o-mini")

    # Tomar los deudores del dataset asignado a la campaña
    debtors = db.query(Debtor).filter(Debtor.debtor_dataset_id == campaign.debtor_dataset_id, Debtor.user_id == user_id).all()

    for debtor in debtors:
        phone = debtor.phone
        whatsapp_phone = f"whatsapp:{phone}"

        # El prompt va como system sin personalizar
        history = [{"role": "system", "content": initial_prompt}]

        personalized_message = personalize_message(message, debtor)

        history.append({"role": "assistant", "content": personalized_message})

        debtor.conversation_history = json.dumps(history)

        send_whatsapp_message(whatsapp_phone, personalized_message)

    db.commit()
