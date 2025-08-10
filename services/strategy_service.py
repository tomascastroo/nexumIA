"""
Este servicio espera que todas las funciones reciban la sesión de base de datos (db: Session) inyectada por el router vía Depends(get_db). No crear la sesión internamente.
"""
from sqlalchemy.orm import Session
from models.Strategy import Strategy
from schemas.campaign import CampaignCreate
from schemas.strategy import StrategyCreate, StrategyUpdate, StrategyOut

# NOTA: Este servicio devuelve objetos ORM. La conversión a Pydantic debe hacerse en el router usando .model_validate(obj, from_attributes=True)
def get_strategy(db: Session, strategy_id: int, user_id: int):
    return db.query(Strategy).filter(Strategy.id == strategy_id, Strategy.user_id == user_id).first()

def get_strategies(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    return db.query(Strategy).filter(Strategy.user_id == user_id).offset(skip).limit(limit).all()

def create_strategy(db: Session, strategy: StrategyCreate, user_id: int):
    # Asegura que rules_by_state es serializable
    rules_by_state_serializable = {}
    for k, v in strategy.rules_by_state.items():
        if hasattr(v, 'dict'):
            rules_by_state_serializable[k] = v.dict()
        else:
            rules_by_state_serializable[k] = v
    
    # Asegura que evaluable_rules es serializable
    evaluable_rules_serializable = []
    if strategy.evaluable_rules:
        for rule in strategy.evaluable_rules:
            if hasattr(rule, 'dict'):
                evaluable_rules_serializable.append(rule.dict())
            else:
                evaluable_rules_serializable.append(rule)
    
    db_strategy = Strategy(
        name=strategy.name,
        initial_prompt=strategy.initial_prompt,
        rules_by_state=rules_by_state_serializable,
        evaluable_rules=evaluable_rules_serializable,
        strict_mode=strategy.strict_mode,
        fallback_prompt=strategy.fallback_prompt,
        user_id=user_id
    )
    db.add(db_strategy)
    db.commit()
    db.refresh(db_strategy)
    return db_strategy

def update_strategy(db: Session, strategy_id: int, strategy: StrategyUpdate, user_id: int):
    db_strategy = get_strategy(db, strategy_id, user_id)
    if not db_strategy:
        return None
    
    # Actualizar campos básicos
    if strategy.name is not None:
        db_strategy.name = strategy.name
    if strategy.initial_prompt is not None:
        db_strategy.initial_prompt = strategy.initial_prompt
    
    # Actualizar rules_by_state si se proporciona
    if strategy.rules_by_state is not None:
        rules_by_state_serializable = {}
        for k, v in strategy.rules_by_state.items():
            if hasattr(v, 'dict'):
                rules_by_state_serializable[k] = v.dict()
            else:
                rules_by_state_serializable[k] = v
        db_strategy.rules_by_state = rules_by_state_serializable
    
    # Actualizar evaluable_rules si se proporciona
    if strategy.evaluable_rules is not None:
        evaluable_rules_serializable = []
        for rule in strategy.evaluable_rules:
            if hasattr(rule, 'dict'):
                evaluable_rules_serializable.append(rule.dict())
            else:
                evaluable_rules_serializable.append(rule)
        db_strategy.evaluable_rules = evaluable_rules_serializable
    
    # Actualizar strict_mode si se proporciona
    if strategy.strict_mode is not None:
        db_strategy.strict_mode = strategy.strict_mode
    
    # Actualizar fallback_prompt si se proporciona
    if strategy.fallback_prompt is not None:
        db_strategy.fallback_prompt = strategy.fallback_prompt
    
    db.commit()
    db.refresh(db_strategy)
    return db_strategy

def delete_strategy(db: Session, strategy_id: int, user_id: int):
    db_strategy = get_strategy(db, strategy_id, user_id)
    if not db_strategy:
        return None
    db.delete(db_strategy)
    db.commit()
    return db_strategy
