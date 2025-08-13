import asyncio
import logging
from typing import Any, Callable, Optional, Dict
from functools import wraps
import time
from datetime import datetime
import json
from dataclasses import dataclass
from enum import Enum

# Configurar logging estructurado
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ErrorSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class ErrorContext:
    """Contexto del error para logging y debugging"""
    service: str
    operation: str
    user_id: Optional[int] = None
    debtor_id: Optional[int] = None
    campaign_id: Optional[int] = None
    strategy_id: Optional[int] = None
    additional_data: Optional[Dict[str, Any]] = None
    severity: ErrorSeverity = ErrorSeverity.MEDIUM

class RetryConfig:
    """Configuración para retry con backoff exponencial"""
    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter

class CircuitBreaker:
    """Circuit breaker para servicios externos"""
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN

    def can_execute(self) -> bool:
        if self.state == "CLOSED":
            return True
        elif self.state == "OPEN":
            if self.last_failure_time is not None and time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = "HALF_OPEN"
                return True
            return False
        else:  # HALF_OPEN
            return True

    def on_success(self):
        self.failure_count = 0
        self.state = "CLOSED"

    def on_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"

class ErrorHandlingService:
    """Servicio centralizado para manejo de errores"""
    
    def __init__(self):
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.rate_limiters: Dict[str, Dict[str, Any]] = {}
        
    def get_circuit_breaker(self, service_name: str) -> CircuitBreaker:
        """Obtiene o crea un circuit breaker para un servicio"""
        if service_name not in self.circuit_breakers:
            self.circuit_breakers[service_name] = CircuitBreaker()
        return self.circuit_breakers[service_name]
    
    def log_error(self, error: Exception, context: ErrorContext):
        """Log estructurado de errores"""
        error_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "service": context.service,
            "operation": context.operation,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "severity": context.severity.value,
            "user_id": context.user_id,
            "debtor_id": context.debtor_id,
            "campaign_id": context.campaign_id,
            "strategy_id": context.strategy_id,
            "additional_data": context.additional_data
        }
        
        log_level = logging.ERROR if context.severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL] else logging.WARNING
        logger.log(log_level, f"Error in {context.service}.{context.operation}: {json.dumps(error_data)}")
        
        # Si es crítico, enviar alerta (implementar integración con sistema de alertas)
        if context.severity == ErrorSeverity.CRITICAL:
            self._send_critical_alert(error_data)
    
    def _send_critical_alert(self, error_data: Dict[str, Any]):
        """Envía alerta crítica (implementar con sistema de notificaciones)"""
        # TODO: Integrar con sistema de notificaciones (Slack, email, etc.)
        logger.critical(f"CRITICAL ALERT: {json.dumps(error_data)}")
    
    def retry_with_backoff(
        self,
        func: Callable,
        retry_config: Optional[RetryConfig] = None,
        context: Optional[ErrorContext] = None
    ):
        """Decorator para retry con backoff exponencial"""
        if retry_config is None:
            retry_config = RetryConfig()
        
        def decorator(*args, **kwargs):
            last_exception: Optional[Exception] = None
            
            for attempt in range(retry_config.max_retries + 1):
                try:
                    result = func(*args, **kwargs)
                    
                    # Si es async, manejar correctamente
                    if asyncio.iscoroutine(result):
                        return result
                    return result
                    
                except Exception as e:
                    last_exception = e
                    
                    if context:
                        self.log_error(e, context)
                    
                    if attempt == retry_config.max_retries:
                        # Último intento falló
                        if context:
                            context.severity = ErrorSeverity.CRITICAL
                            self.log_error(e, context)
                        raise e
                    
                    # Calcular delay con backoff exponencial
                    delay = min(
                        retry_config.base_delay * (retry_config.exponential_base ** attempt),
                        retry_config.max_delay
                    )
                    
                    if retry_config.jitter:
                        delay *= (0.5 + 0.5 * time.time() % 1)
                    
                    logger.warning(f"Retry attempt {attempt + 1}/{retry_config.max_retries} failed. Retrying in {delay:.2f}s")
                    time.sleep(delay)
            
            if last_exception:
                raise last_exception
            else:
                raise Exception("Unexpected error in retry logic")
        
        return decorator
    
    def rate_limit(self, service_name: str, max_requests: int = 100, window_seconds: int = 60):
        """Decorator para rate limiting"""
        def decorator(func: Callable):
            @wraps(func)
            def wrapper(*args, **kwargs):
                current_time = time.time()
                
                if service_name not in self.rate_limiters:
                    self.rate_limiters[service_name] = {
                        'requests': [],
                        'max_requests': max_requests,
                        'window_seconds': window_seconds
                    }
                
                limiter = self.rate_limiters[service_name]
                
                # Limpiar requests antiguos
                limiter['requests'] = [
                    req_time for req_time in limiter['requests']
                    if current_time - req_time < window_seconds
                ]
                
                # Verificar si podemos hacer la request
                if len(limiter['requests']) >= max_requests:
                    raise Exception(f"Rate limit exceeded for {service_name}")
                
                # Agregar request actual
                limiter['requests'].append(current_time)
                
                return func(*args, **kwargs)
            
            return wrapper
        return decorator
    
    def circuit_breaker(self, service_name: str):
        """Decorator para circuit breaker"""
        def decorator(func: Callable):
            @wraps(func)
            def wrapper(*args, **kwargs):
                cb = self.get_circuit_breaker(service_name)
                
                if not cb.can_execute():
                    raise Exception(f"Circuit breaker is OPEN for {service_name}")
                
                try:
                    result = func(*args, **kwargs)
                    cb.on_success()
                    return result
                except Exception as e:
                    cb.on_failure()
                    raise e
            
            return wrapper
        return decorator

# Instancia global del servicio
error_handling_service = ErrorHandlingService()

# Decorators de conveniencia
def retry_on_failure(max_retries: int = 3, context: Optional[ErrorContext] = None):
    """Decorator de conveniencia para retry"""
    def decorator(func: Callable):
        config = RetryConfig(max_retries=max_retries)
        return error_handling_service.retry_with_backoff(func, retry_config=config, context=context)
    return decorator

def rate_limited(service_name: str, max_requests: int = 100, window_seconds: int = 60):
    """Decorator de conveniencia para rate limiting"""
    return error_handling_service.rate_limit(service_name, max_requests, window_seconds)

def circuit_breaker_protected(service_name: str):
    """Decorator de conveniencia para circuit breaker"""
    return error_handling_service.circuit_breaker(service_name) 