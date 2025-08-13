from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from dependencies.auth import get_current_user
from db.db import SessionLocal
from services.traceability_service import traceability_service
from models.User import User

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

router = APIRouter(prefix="/traceability", tags=["traceability"])

@router.get("/decisions")
async def get_decision_history(
    debtor_id: Optional[int] = Query(None, description="Filtrar por ID de deudor"),
    strategy_id: Optional[int] = Query(None, description="Filtrar por ID de estrategia"),
    limit: int = Query(50, ge=1, le=100, description="Límite de resultados"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtiene el historial de decisiones de reglas con filtros opcionales.
    """
    try:
        decisions = traceability_service.get_decision_history(
            debtor_id=debtor_id,
            strategy_id=strategy_id,
            limit=limit
        )
        
        return {
            "success": True,
            "data": decisions,
            "total": len(decisions),
            "filters": {
                "debtor_id": debtor_id,
                "strategy_id": strategy_id,
                "limit": limit
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo historial: {str(e)}")

@router.get("/analytics")
async def get_decision_analytics(
    debtor_id: Optional[int] = Query(None, description="Filtrar por ID de deudor"),
    strategy_id: Optional[int] = Query(None, description="Filtrar por ID de estrategia"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtiene analytics de las decisiones de reglas.
    """
    try:
        analytics = traceability_service.get_decision_analytics(
            debtor_id=debtor_id,
            strategy_id=strategy_id
        )
        
        return {
            "success": True,
            "data": analytics
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo analytics: {str(e)}")

@router.get("/export")
async def export_decision_logs(
    debtor_id: Optional[int] = Query(None, description="Filtrar por ID de deudor"),
    strategy_id: Optional[int] = Query(None, description="Filtrar por ID de estrategia"),
    format: str = Query("json", description="Formato de exportación (json, csv)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Exporta los logs de decisiones en diferentes formatos.
    """
    try:
        if format not in ["json", "csv"]:
            raise HTTPException(status_code=400, detail="Formato no soportado. Use 'json' o 'csv'")
        
        exported_data = traceability_service.export_decision_logs(
            debtor_id=debtor_id,
            strategy_id=strategy_id,
            format=format
        )
        
        return {
            "success": True,
            "data": exported_data,
            "format": format,
            "filters": {
                "debtor_id": debtor_id,
                "strategy_id": strategy_id
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exportando logs: {str(e)}")

@router.delete("/clear")
async def clear_decision_logs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Limpia todos los logs de decisiones (solo para testing).
    """
    try:
        traceability_service.clear_logs()
        
        return {
            "success": True,
            "message": "Logs de decisiones limpiados exitosamente"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error limpiando logs: {str(e)}") 