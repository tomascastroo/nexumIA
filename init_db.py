from db.db import Base, engine
from models.Debtor import Debtor
from models.Campaign import Campaign
from models.Strategy import Strategy
from models.Bot import Bot
from models.User import User
from models.DebtorDataset import DebtorDataset
from models.DebtorCustomField import DebtorCustomField
print("Creando tablas en PostgreSQL...")
Base.metadata.create_all(bind=engine)
