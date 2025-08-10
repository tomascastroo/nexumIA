from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from dependencies.auth import get_current_user
from models.User import User
from services import strategy_service
from db.db import get_db
from schemas.strategy import StrategyCreate, StrategyUpdate, StrategyRead
from sqlalchemy.exc import IntegrityError

router = APIRouter(
    tags=["Strategies"],
)

@router.post("/", response_model=StrategyRead)
def create_strategy(
    strategy: StrategyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        return strategy_service.create_strategy(db, strategy, user_id=current_user.id)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Ya existe una estrategia con ese nombre.")

@router.put("/{strategy_id}", response_model=StrategyRead)
def update_strategy(
    strategy_id: int,
    strategy: StrategyUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_strategy = strategy_service.update_strategy(db, strategy_id, strategy, user_id=current_user.id)
    if db_strategy is None:
        raise HTTPException(status_code=404, detail="Strategy not found")
    return db_strategy

@router.get("/{strategy_id}", response_model=StrategyRead)
def get_strategy(
    strategy_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_strategy = strategy_service.get_strategy(db, strategy_id, user_id=current_user.id)
    if db_strategy is None:
        raise HTTPException(status_code=404, detail="Strategy not found")
    return db_strategy

@router.get("/", response_model=list[StrategyRead])
def get_strategies(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return strategy_service.get_strategies(db, user_id=current_user.id, skip=skip, limit=limit)

@router.delete("/{strategy_id}", response_model=StrategyRead)
def delete_strategy(
    strategy_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_strategy = strategy_service.delete_strategy(db, strategy_id, user_id=current_user.id)
    if db_strategy is None:
        raise HTTPException(status_code=404, detail="Strategy not found")
    return db_strategy
