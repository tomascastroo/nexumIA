from sqlalchemy import Column, DateTime, Integer, String, ForeignKey, func
from sqlalchemy.orm import relationship
from db.db import Base

class DebtorCustomField(Base):
    __tablename__ = "debtor_custom_fields"

    id = Column(Integer, primary_key=True, index=True)
    debtor_dataset_id = Column(Integer, ForeignKey("debtor_datasets.id"), nullable=False)
    name = Column(String, nullable=False)
    field_type = Column(String, nullable=False, default="string")  # ej: string, float, date
    debtor_dataset = relationship("DebtorDataset", back_populates="custom_fields")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
