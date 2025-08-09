from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from core.security import create_access_token, hash_password, verify_password, ACCESS_TOKEN_EXPIRE_MINUTES
from db.db import SessionLocal
from models.User import User
from schemas.user import UserCreate, UserLogin, UserOut, TokenData, UserResponse, LoginResponse
from datetime import datetime, timedelta
from pydantic import BaseModel, ConfigDict
from fastapi_limiter.depends import RateLimiter
from dependencies.auth import get_current_user, require_roles
from core.logger import log_security_event
from core.metrics import record_security_event

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/register", response_model=UserOut)
def register(user: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(status_code=400, detail="El email ya está registrado")
    hashed_pw = hash_password(user.password)
    db_user = User(email=user.email,hashed_password=hashed_pw)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    log_security_event("user_registered", user_id=db_user.id)
    record_security_event("user_registered", ip_address="-")
    return UserOut.model_validate(db_user, from_attributes=True)

@router.post("/login", response_model=LoginResponse, dependencies=[Depends(RateLimiter(times=5, seconds=60))])
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if not db_user or not verify_password(user.password, str(db_user.hashed_password)):
        log_security_event("login_failed", user_id=None, details={"email": user.email})
        record_security_event("login_failed", ip_address="-")
        raise HTTPException(status_code=400, detail="Invalid credentials")
    
    expires_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token({"sub": str(db_user.id)}, expires_delta=expires_delta)
    expires_at = int((datetime.utcnow() + expires_delta).timestamp())
    
    log_security_event("login_success", user_id=db_user.id)
    record_security_event("login_success", ip_address="-")
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_at": expires_at,
        "user": UserResponse.model_validate(db_user, from_attributes=True)
    }

@router.get("/whoami", response_model=UserOut)
def whoami(current_user: User = Depends(get_current_user)):
    return UserOut.model_validate(current_user, from_attributes=True)

@router.get("/admin/ping", dependencies=[Depends(require_roles("admin"))])
def admin_ping():
    return {"status": "ok", "role": "admin"}