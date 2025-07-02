from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from core.security import create_access_token, hash_password, verify_password, ACCESS_TOKEN_EXPIRE_MINUTES
from db.db import SessionLocal
from models.User import User
from schemas.user import UserCreate, UserLogin, UserOut, Token, TokenData
from datetime import datetime, timedelta

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
    return db_user

@router.post("/login", response_model=Token)
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if not db_user or not verify_password(user.password, str(db_user.hashed_password)):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    
    # Generate a token with expiration
    expires_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token({"sub": str(db_user.id)}, expires_delta=expires_delta)
    
    # Calculate expiration timestamp for the frontend
    expires_at = int((datetime.utcnow() + expires_delta).timestamp())
    
    return {"access_token": access_token, "token_type": "bearer", "expires_at": expires_at}