from pytest import Session
from models.Strategy import Strategy
from db.db import SessionLocal
from schemas.campaign import CampaignCreate
from schemas.strategy import StrategyCreate, StrategyUpdate

def get_startegy(db: Session, strategy_id: int, user_id: int):
    return db.query(Strategy).filter(Strategy.id == strategy_id, Strategy.user_id == user_id).first()

def get_strategies(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    return db.query(Strategy).filter(Strategy.user_id == user_id).offset(skip).limit(limit).all()

def create_strategy(db: Session, strategy: StrategyCreate, user_id: int):
    db_strategy = Strategy(name=strategy.name,initial_prompt=strategy.initial_prompt, rules_by_state=strategy.rules_by_state, user_id=user_id)
    db.add(db_strategy)
    db.commit()
    db.refresh(db_strategy)
    return db_strategy

def update_strategy(db:Session,strategy_id:int, strategy:StrategyUpdate,user_id: int):
    db_strategy = get_startegy(db,strategy_id,user_id)
    if not db_strategy:
        return  None
    for var, value in vars(strategy).items():
        setattr(db_strategy,var,value) if value else None
    db.commit()
    db.refresh(db_strategy)
    return db_strategy

def delete_strategy(db:Session,strategy_id:int,user_id: int):
    db_strategy = get_startegy(db,strategy_id,user_id)
    if not db_strategy:
        return None
    db.delete(db_strategy)
    db.commit()
    return db_strategy
