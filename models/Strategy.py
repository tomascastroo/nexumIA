from typing import Any, Dict, List
from sqlalchemy import String, DateTime, func, JSON, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime

from db.db import Base


class Strategy(Base):
    __tablename__ = "strategies"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, unique=True, index=True)
    initial_prompt: Mapped[str] = mapped_column(String, default="")
    
    # Nuevo sistema de reglas evaluables
    evaluable_rules: Mapped[List[Dict[str, Any]]] = mapped_column(
        JSON, 
        default=lambda: [],
        comment="Reglas evaluables con condiciones, respuestas y flags de estrictez"
    )
    
    # Reglas por estado (mantener compatibilidad)
    rules_by_state: Mapped[Dict[str, List[Dict[str, Any]]]] = mapped_column(
        JSON, 
        default=lambda: {},
        comment="Reglas por estado (legacy - mantener compatibilidad)"
    )
    
    # Configuración de estrictez global
    strict_mode: Mapped[bool] = mapped_column(
        Boolean, 
        default=False,
        comment="Modo estricto global: solo respuestas autorizadas"
    )
    
    # Configuración de fallback
    fallback_prompt: Mapped[str] = mapped_column(
        String, 
        default="",
        comment="Prompt de fallback cuando no se cumplen reglas"
    )
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    user = relationship("User", back_populates="strategies")

    campaigns = relationship("Campaign", back_populates="strategy")

    def __repr__(self):
        return f"<Strategy(id={self.id}, name='{self.name}')>"