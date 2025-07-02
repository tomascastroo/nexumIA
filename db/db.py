from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

SQLALCHEMY_DATABASE_URL = "postgresql://postgres:apache@localhost:5432/bots_de_cobranza"

engine = create_engine(SQLALCHEMY_DATABASE_URL)  # sin connect_args

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
