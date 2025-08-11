from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from dependencies.auth import get_current_user
from models.User import User
from schemas.campaign import CampaignCreate, CampaignRead, CampaignUpdate
from services import campaign_service
from db.db import SessionLocal

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=CampaignRead)
def create_campaign(campaign: CampaignCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return campaign_service.create_campaign(db, campaign, current_user.id)

@router.get("/{campaign_id}", response_model=CampaignRead)
def get_campaign(campaign_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    campaign = campaign_service.get_campaign(db, campaign_id, current_user.id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return campaign

@router.get("/", response_model=list[CampaignRead])
def get_campaigns(db: Session = Depends(get_db), current_user: User = Depends(get_current_user), skip: int = 0, limit: int = 100):
    return campaign_service.get_campaigns(db, current_user.id, skip, limit)

@router.put("/{campaign_id}", response_model=CampaignRead)
def update_campaign(campaign_id: int, campaign: CampaignUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    updated = campaign_service.update_campaign(db, campaign_id, campaign, current_user.id)
    if not updated:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return updated

@router.delete("/{campaign_id}", response_model=CampaignRead)
def delete_campaign(campaign_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    deleted = campaign_service.delete_campaign(db, campaign_id, current_user.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return deleted

@router.get("/throw-campaign/{campaign_id}")
def launch_campaign(campaign_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    campaign_service.throw_campaign(db, campaign_id, current_user.id)
    return {"status": "launched"}
