from typing import List
from fastapi import APIRouter, Body, Depends, HTTPException
from openai import BaseModel
from sqlalchemy.orm import Session
from models.User import User
from models.Debtor import Debtor
from models.Campaign import Campaign
from dependencies.auth import get_current_user
from services import campaign_service
from db.db import SessionLocal
from schemas.campaign import CampaignBase, CampaignRead, CampaignUpdate, CampaignCreate
from services import debtor_service


router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/",response_model=CampaignCreate)
def create_campaign(campaign: CampaignCreate,db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return campaign_service.create_campaign(db,campaign,user_id=current_user.id)


@router.get("/{campaign_id}",response_model=CampaignRead)
def get_campaign(campaign_id:int,
                 db:Session = Depends(get_db),
                 current_user: User = Depends(get_current_user)):
    db_campaign = campaign_service.get_campaign(db,campaign_id,user_id=current_user.id)
    if db_campaign is None:
       raise HTTPException(status_code=404, detail="Campaign not found")
    return db_campaign

@router.get("/",response_model=list[CampaignRead])
def get_campaigns(skip: int = 0,limit:int = 100,
                  current_user: User = Depends(get_current_user),
                  db:Session = Depends(get_db)):
    return campaign_service.get_campaigns(db,user_id=current_user.id,skip=skip,limit=limit)

@router.delete("/{campaign_id}",response_model=CampaignRead)
def delete_campaign(campaign_id:int,db:Session = Depends(get_db),current_user: User = Depends(get_current_user)):
    db_campaign = campaign_service.delete_campaign(db,campaign_id,current_user,user_id=current_user.id)
    if db_campaign is None:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return db_campaign


@router.put("/{campaign_id}", response_model=CampaignRead)
def update_campaign(campaign_id: int, campaign: CampaignUpdate, db: Session = Depends(get_db),current_user: User = Depends(get_current_user)):
    db_campaign = campaign_service.update_campaign(db, campaign_id, campaign,user_id=current_user.id)
    if db_campaign is None:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return db_campaign


@router.get("/throw-campaign/{campaign_id}")
def throw_campaign(campaign_id: int, db: Session = Depends(get_db),current_user: User = Depends(get_current_user)):
    campaign_service.throw_campaign(db, campaign_id,user_id=current_user.id)
    return {"status": "launched"}




@router.post("/{campaign_id}/debtors")
def add_debtors_to_campaign(
    campaign_id: int,
    debtor_ids: List[int] = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # CAMBIE ACA
    # Validaciones y búsqueda
    campaign = campaign_service.get_campaign(db=db, campaign_id=campaign_id, user_id=current_user.id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    debtors = db.query(Debtor).filter(Debtor.id.in_(debtor_ids), Debtor.user_id == current_user.id).all()
    if not debtors:
        raise HTTPException(status_code=404, detail="No debtors found")
    if len(debtors) != len(debtor_ids):
        raise HTTPException(status_code=404, detail="One or more debtors not found")

    # Asignar deudores
    for debtor in debtors:
        debtor.campaign = campaign  # Esto asigna el campaign_id en la tabla debtors

    db.commit()

    return {"message": f"{len(debtors)} debtors added to campaign {campaign_id}"}

