from datetime import datetime
from sqlalchemy import Column, DateTime,Integer,String,Date,ForeignKey
from sqlalchemy.orm import relationship
from db.db import Base

class Campaign(Base):
    __tablename__ = "campaigns"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)

    bot_id = Column(Integer, ForeignKey("bots.id"))
    strategy_id = Column(Integer, ForeignKey("strategies.id"))

    status = Column(String, default="inactive")
    start_date = Column(DateTime, default=datetime.utcnow)
    end_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    bot = relationship("Bot", back_populates="campaigns")
    strategy = relationship("Strategy", back_populates="campaigns")
    debtors = relationship("Debtor", back_populates="campaign")
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="campaigns")