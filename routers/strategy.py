from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from dependencies.auth import get_current_user
from models.User import User
from services import strategy_service
from db.db import SessionLocal
from schemas.strategy import StrategyCreate, StrategyUpdate, StrategyRead

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=StrategyCreate)
def create_strategy(
    strategy: StrategyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return strategy_service.create_strategy(db, strategy, user_id=current_user.id)

@router.post("/{strategy_id}",response_model=StrategyUpdate)
def update_strategy(
    strategy_id:int, 
    strategy:StrategyUpdate,
    db:Session=Depends(get_db),
    current_user: User = Depends(get_current_user)
    ):
    db_strategy = strategy_service.update_strategy(db,strategy_id,strategy,user_id=current_user.id)
    if db_strategy is None:
        raise HTTPException(status_code=404, detail="Strategy not found")
    return db_strategy

@router.get("/{strategy_id}",response_model=StrategyRead,)
def get_strategy(strategy_id:int,db:Session = Depends(get_db),current_user: User = Depends(get_current_user)):
    db_strategy= strategy_service.get_startegy(db, strategy_id,user_id=current_user.id)
    if  db_strategy is None:
        raise HTTPException(status_code=404,detail="Strategy not found")
    return db_strategy

@router.get("/",response_model=list[StrategyRead])
def get_strategies(skip: int = 0,limit:int = 100,db:Session = Depends(get_db),current_user: User = Depends(get_current_user)):
    return strategy_service.get_strategies(db,user_id=current_user.id,skip=skip,limit=limit)

@router.delete("/{strategy_id}",response_model=StrategyRead)
def delete_strategy(strategy_id:int,db:Session = Depends(get_db),current_user: User = Depends(get_current_user)):
    db_strategy = strategy_service.delete_strategy(db,strategy_id,user_id=current_user.id)
    if db_strategy is None:
        raise HTTPException(status_code=404,detail="Strategy not found")
    return db_strategy

