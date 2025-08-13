import os
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Response, APIRouter
from dotenv import load_dotenv

load_dotenv()

class MetricsCollector:
    """Sistema de métricas con Prometheus para monitoreo de producción"""
    
    def __init__(self):
        self.enable_metrics = os.getenv("ENABLE_METRICS", "true").lower() == "true"
        
        if self.enable_metrics:
            self._setup_metrics()
    
    def _setup_metrics(self):
        """Configurar métricas de Prometheus"""
        
        # Métricas de HTTP
        self.http_requests_total = Counter(
            'http_requests_total',
            'Total HTTP requests',
            ['method', 'endpoint', 'status_code']
        )
        
        self.http_request_duration_seconds = Histogram(
            'http_request_duration_seconds',
            'HTTP request duration in seconds',
            ['method', 'endpoint']
        )
        
        # Métricas de negocio
        self.debtors_total = Gauge(
            'debtors_total',
            'Total number of debtors',
            ['state', 'dataset_id']
        )
        
        self.campaigns_active = Gauge(
            'campaigns_active',
            'Number of active campaigns',
            ['user_id']
        )
        
        self.payments_total = Counter(
            'payments_total',
            'Total payments processed',
            ['status', 'campaign_id']
        )
        
        self.payment_amount_total = Counter(
            'payment_amount_total',
            'Total payment amounts',
            ['status', 'campaign_id']
        )
        
        # Métricas de IA
        self.ai_requests_total = Counter(
            'ai_requests_total',
            'Total AI API requests',
            ['service', 'status']
        )
        
        self.ai_response_time_seconds = Histogram(
            'ai_response_time_seconds',
            'AI API response time in seconds',
            ['service']
        )
        
        # Métricas de sistema
        self.database_connections_active = Gauge(
            'database_connections_active',
            'Active database connections'
        )
        
        self.redis_connections_active = Gauge(
            'redis_connections_active',
            'Active Redis connections'
        )
        
        # Métricas de errores
        self.errors_total = Counter(
            'errors_total',
            'Total errors',
            ['error_type', 'endpoint']
        )
        
        # Métricas de seguridad
        self.security_events_total = Counter(
            'security_events_total',
            'Total security events',
            ['event_type', 'ip_address']
        )
        
        self.rate_limit_exceeded_total = Counter(
            'rate_limit_exceeded_total',
            'Total rate limit violations',
            ['ip_address']
        )
    
    def record_http_request(self, method: str, endpoint: str, status_code: int, duration: float):
        """Registrar métrica de request HTTP"""
        if not self.enable_metrics:
            return
        
        self.http_requests_total.labels(method=method, endpoint=endpoint, status_code=status_code).inc()
        self.http_request_duration_seconds.labels(method=method, endpoint=endpoint).observe(duration)
    
    def record_debtor_count(self, state: str, dataset_id: int, count: int):
        """Registrar métrica de cantidad de deudores"""
        if not self.enable_metrics:
            return
        
        self.debtors_total.labels(state=state, dataset_id=str(dataset_id)).set(count)
    
    def record_campaign_count(self, user_id: int, count: int):
        """Registrar métrica de cantidad de campañas"""
        if not self.enable_metrics:
            return
        
        self.campaigns_active.labels(user_id=str(user_id)).set(count)
    
    def record_payment(self, status: str, campaign_id: int, amount: float = 0):
        """Registrar métrica de pago"""
        if not self.enable_metrics:
            return
        
        self.payments_total.labels(status=status, campaign_id=str(campaign_id)).inc()
        if amount > 0:
            self.payment_amount_total.labels(status=status, campaign_id=str(campaign_id)).inc(amount)
    
    def record_ai_request(self, service: str, status: str, duration: float):
        """Registrar métrica de request a IA"""
        if not self.enable_metrics:
            return
        
        self.ai_requests_total.labels(service=service, status=status).inc()
        self.ai_response_time_seconds.labels(service=service).observe(duration)
    
    def record_error(self, error_type: str, endpoint: str):
        """Registrar métrica de error"""
        if not self.enable_metrics:
            return
        
        self.errors_total.labels(error_type=error_type, endpoint=endpoint).inc()
    
    def record_security_event(self, event_type: str, ip_address: str):
        """Registrar métrica de evento de seguridad"""
        if not self.enable_metrics:
            return
        
        self.security_events_total.labels(event_type=event_type, ip_address=ip_address).inc()
    
    def record_rate_limit_violation(self, ip_address: str):
        """Registrar métrica de violación de rate limit"""
        if not self.enable_metrics:
            return
        
        self.rate_limit_exceeded_total.labels(ip_address=ip_address).inc()
    
    def set_database_connections(self, count: int):
        """Establecer métrica de conexiones de base de datos"""
        if not self.enable_metrics:
            return
        
        self.database_connections_active.set(count)
    
    def set_redis_connections(self, count: int):
        """Establecer métrica de conexiones de Redis"""
        if not self.enable_metrics:
            return
        
        self.redis_connections_active.set(count)

# Instancia global del collector
metrics_collector = MetricsCollector()

# Funciones de conveniencia
def record_http_request(method: str, endpoint: str, status_code: int, duration: float):
    metrics_collector.record_http_request(method, endpoint, status_code, duration)

def record_debtor_count(state: str, dataset_id: int, count: int):
    metrics_collector.record_debtor_count(state, dataset_id, count)

def record_campaign_count(user_id: int, count: int):
    metrics_collector.record_campaign_count(user_id, count)

def record_payment(status: str, campaign_id: int, amount: float = 0):
    metrics_collector.record_payment(status, campaign_id, amount)

def record_ai_request(service: str, status: str, duration: float):
    metrics_collector.record_ai_request(service, status, duration)

def record_error(error_type: str, endpoint: str):
    metrics_collector.record_error(error_type, endpoint)

def record_security_event(event_type: str, ip_address: str):
    metrics_collector.record_security_event(event_type, ip_address)

def record_rate_limit_violation(ip_address: str):
    metrics_collector.record_rate_limit_violation(ip_address)

def get_metrics():
    """Obtener métricas en formato Prometheus"""
    if not metrics_collector.enable_metrics:
        return ""
    
    return generate_latest()

# Métricas de cache
cache_hit_counter = Counter('cache_hits', 'Cache hits')
cache_miss_counter = Counter('cache_misses', 'Cache misses')

# Métricas de Celery (importadas en tasks)
# whatsapp_messages_sent, ia_tasks_executed

router = APIRouter()

@router.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST) 