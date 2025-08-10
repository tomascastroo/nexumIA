import os
import sys
import json
from datetime import datetime
from typing import Any, Dict, Optional
from loguru import logger
from dotenv import load_dotenv

load_dotenv()

class StructuredLogger:
    """Sistema de logging estructurado para producción"""
    
    def __init__(self):
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        self.environment = os.getenv("ENVIRONMENT", "development")
        self.setup_logger()
    
    def setup_logger(self):
        """Configurar logger con formato estructurado"""
        # Remover logger por defecto
        logger.remove()
        
        # Configurar formato JSON para producción
        if self.environment == "production":
            logger.add(
                sys.stdout,
                format=self._json_formatter,
                level=self.log_level,
                serialize=True
            )
            
            # Log a archivo en producción
            logger.add(
                "logs/app.log",
                format=self._json_formatter,
                level=self.log_level,
                serialize=True,
                rotation="100 MB",
                retention="30 days",
                compression="zip"
            )
        else:
            # Formato legible para desarrollo
            logger.add(
                sys.stdout,
                format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
                level=self.log_level
            )
    
    def _json_formatter(self, record: Dict[str, Any]) -> str:
        """Formatear log como JSON estructurado"""
        log_entry = {
            "timestamp": datetime.fromtimestamp(record["time"].timestamp()).isoformat(),
            "level": record["level"].name,
            "message": record["message"],
            "module": record["module"],
            "function": record["function"],
            "line": record["line"],
            "environment": self.environment
        }
        
        # Agregar campos extra si existen
        if "extra" in record and record["extra"]:
            log_entry.update(record["extra"])
        
        return json.dumps(log_entry)
    
    def log_request(self, request_id: str, method: str, url: str, status_code: int, 
                   user_id: Optional[int] = None, duration: Optional[float] = None):
        """Log de requests HTTP"""
        logger.info(
            "HTTP Request",
            extra={
                "request_id": request_id,
                "method": method,
                "url": url,
                "status_code": status_code,
                "user_id": user_id,
                "duration_ms": round(duration * 1000, 2) if duration else None,
                "log_type": "http_request"
            }
        )
    
    def log_error(self, error: Exception, context: Dict[str, Any] = None):
        """Log de errores con contexto"""
        logger.error(
            f"Error: {str(error)}",
            extra={
                "error_type": type(error).__name__,
                "error_message": str(error),
                "context": context or {},
                "log_type": "error"
            }
        )
    
    def log_security_event(self, event_type: str, user_id: Optional[int] = None, 
                          ip_address: Optional[str] = None, details: Dict[str, Any] = None):
        """Log de eventos de seguridad"""
        logger.warning(
            f"Security Event: {event_type}",
            extra={
                "event_type": event_type,
                "user_id": user_id,
                "ip_address": ip_address,
                "details": details or {},
                "log_type": "security"
            }
        )
    
    def log_business_event(self, event_type: str, user_id: Optional[int] = None,
                          debtor_id: Optional[int] = None, campaign_id: Optional[int] = None,
                          details: Dict[str, Any] = None):
        """Log de eventos de negocio"""
        logger.info(
            f"Business Event: {event_type}",
            extra={
                "event_type": event_type,
                "user_id": user_id,
                "debtor_id": debtor_id,
                "campaign_id": campaign_id,
                "details": details or {},
                "log_type": "business"
            }
        )
    
    def log_performance(self, operation: str, duration: float, 
                       user_id: Optional[int] = None, details: Dict[str, Any] = None):
        """Log de métricas de performance"""
        logger.info(
            f"Performance: {operation}",
            extra={
                "operation": operation,
                "duration_ms": round(duration * 1000, 2),
                "user_id": user_id,
                "details": details or {},
                "log_type": "performance"
            }
        )

# Instancia global del logger
structured_logger = StructuredLogger()

# Funciones de conveniencia
def log_request(request_id: str, method: str, url: str, status_code: int, 
                user_id: Optional[int] = None, duration: Optional[float] = None):
    structured_logger.log_request(request_id, method, url, status_code, user_id, duration)

def log_error(error: Exception, context: Dict[str, Any] = None):
    structured_logger.log_error(error, context)

def log_security_event(event_type: str, user_id: Optional[int] = None, 
                      ip_address: Optional[str] = None, details: Dict[str, Any] = None):
    structured_logger.log_security_event(event_type, user_id, ip_address, details)

def log_business_event(event_type: str, user_id: Optional[int] = None,
                      debtor_id: Optional[int] = None, campaign_id: Optional[int] = None,
                      details: Dict[str, Any] = None):
    structured_logger.log_business_event(event_type, user_id, debtor_id, campaign_id, details)

def log_performance(operation: str, duration: float, 
                   user_id: Optional[int] = None, details: Dict[str, Any] = None):
    structured_logger.log_performance(operation, duration, user_id, details) 