import os
from fastapi import HTTPException, status
from passlib.context import CryptContext
from jose import JWTError, jwt 
from datetime import datetime,timedelta
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# JWT
def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code= status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )



# HASHED PASSWORD

pwd_context = CryptContext(schemes=["bcrypt"],deprecated="auto")

def hash_password(password:str)-> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str,hashed_password:str)-> bool:
    return pwd_context.verify(plain_password,hashed_password)



