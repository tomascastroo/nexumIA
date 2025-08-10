"""
Middleware de rate limiting para limitar peticiones por IP.
Configurable con RATE_LIMIT_MAX y RATE_LIMIT_WINDOW en segundos.
"""
import time
import hashlib
from typing import Optional
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
import redis
import os
from core.logger import logger

# Configuración desde variables de entorno
RATE_LIMIT_MAX = int(os.getenv("RATE_LIMIT_MAX", "100"))
RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "3600"))  # 1 hora por defecto

# Configuración de Redis
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))

def get_redis_client() -> redis.Redis:
    """Obtiene cliente Redis configurado."""
    try:
        if REDIS_URL != "redis://localhost:6379/0":
            return redis.from_url(REDIS_URL)
        else:
            return redis.Redis(
                host=REDIS_HOST,
                port=REDIS_PORT,
                db=REDIS_DB,
                decode_responses=True
            )
    except Exception as e:
        logger.error(f"Error conectando a Redis: {e}")
        return None

def get_client_ip(request: Request) -> str:
    """Extrae la IP real del cliente considerando proxies."""
    # Verificar headers de proxy
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # IP directa
    return request.client.host if request.client else "unknown"

def generate_rate_limit_key(ip: str, endpoint: str) -> str:
    """Genera clave única para rate limiting."""
    window_start = int(time.time() // RATE_LIMIT_WINDOW) * RATE_LIMIT_WINDOW
    key_data = f"{ip}:{endpoint}:{window_start}"
    return f"rate_limit:{hashlib.md5(key_data.encode()).hexdigest()}"

async def rate_limit_middleware(request: Request, call_next):
    """
    Middleware de rate limiting que verifica límites por IP.
    
    Args:
        request: Request de FastAPI
        call_next: Función para continuar el pipeline
        
    Returns:
        Response o HTTPException 429 si se excede el límite
    """
    # Obtener IP del cliente
    client_ip = get_client_ip(request)
    endpoint = request.url.path
    
    # Generar clave para Redis
    rate_key = generate_rate_limit_key(client_ip, endpoint)
    
    # Obtener cliente Redis
    redis_client = get_redis_client()
    
    if redis_client is None:
        # Si Redis no está disponible, permitir la petición
        logger.warning("Redis no disponible, saltando rate limiting")
        response = await call_next(request)
        return response
    
    try:
        # Verificar límite actual
        current_requests = redis_client.get(rate_key)
        current_count = int(current_requests) if current_requests else 0
        
        if current_count >= RATE_LIMIT_MAX:
            logger.warning(f"Rate limit excedido para IP {client_ip} en {endpoint}")
            
            # Calcular tiempo restante
            window_start = int(time.time() // RATE_LIMIT_WINDOW) * RATE_LIMIT_WINDOW
            window_end = window_start + RATE_LIMIT_WINDOW
            reset_time = window_end - int(time.time())
            
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "message": f"Too many requests. Limit: {RATE_LIMIT_MAX} requests per {RATE_LIMIT_WINDOW} seconds",
                    "reset_time": reset_time,
                    "limit": RATE_LIMIT_MAX,
                    "window": RATE_LIMIT_WINDOW
                },
                headers={
                    "X-RateLimit-Limit": str(RATE_LIMIT_MAX),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(window_end),
                    "Retry-After": str(reset_time)
                }
            )
        
        # Incrementar contador
        pipe = redis_client.pipeline()
        pipe.incr(rate_key)
        pipe.expire(rate_key, RATE_LIMIT_WINDOW)
        results = pipe.execute()
        
        new_count = results[0]
        
        # Continuar con la petición
        response = await call_next(request)
        
        # Agregar headers de rate limiting
        response.headers["X-RateLimit-Limit"] = str(RATE_LIMIT_MAX)
        response.headers["X-RateLimit-Remaining"] = str(max(0, RATE_LIMIT_MAX - new_count))
        response.headers["X-RateLimit-Reset"] = str(int(time.time() // RATE_LIMIT_WINDOW) * RATE_LIMIT_WINDOW + RATE_LIMIT_WINDOW)
        
        return response
        
    except Exception as e:
        logger.error(f"Error en rate limiting para IP {client_ip}: {e}")
        # En caso de error, permitir la petición
        response = await call_next(request)
        return response

def get_rate_limit_info(ip: str, endpoint: str) -> dict:
    """
    Obtiene información de rate limiting para una IP y endpoint.
    
    Args:
        ip: IP del cliente
        endpoint: Endpoint de la API
        
    Returns:
        Dict con información de rate limiting
    """
    redis_client = get_redis_client()
    if redis_client is None:
        return {"error": "Redis no disponible"}
    
    try:
        rate_key = generate_rate_limit_key(ip, endpoint)
        current_requests = redis_client.get(rate_key)
        current_count = int(current_requests) if current_requests else 0
        
        window_start = int(time.time() // RATE_LIMIT_WINDOW) * RATE_LIMIT_WINDOW
        window_end = window_start + RATE_LIMIT_WINDOW
        reset_time = window_end - int(time.time())
        
        return {
            "ip": ip,
            "endpoint": endpoint,
            "current_requests": current_count,
            "limit": RATE_LIMIT_MAX,
            "window_seconds": RATE_LIMIT_WINDOW,
            "remaining": max(0, RATE_LIMIT_MAX - current_count),
            "reset_time": reset_time,
            "window_end": window_end
        }
    except Exception as e:
        logger.error(f"Error obteniendo info de rate limiting: {e}")
        return {"error": str(e)} 