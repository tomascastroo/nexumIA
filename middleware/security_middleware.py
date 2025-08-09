import os
import time
import uuid
from typing import Dict, List, Optional
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import Response
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from dotenv import load_dotenv

load_dotenv()

# Configurar rate limiter
limiter = Limiter(key_func=get_remote_address)

class SecurityMiddleware(BaseHTTPMiddleware):
    """Middleware de seguridad para proteger la API"""
    
    def __init__(self, app):
        super().__init__(app)
        self.rate_limit_requests = int(os.getenv("API_RATE_LIMIT", "100"))
        self.rate_limit_window = int(os.getenv("API_RATE_LIMIT_WINDOW", "60"))
        
    async def dispatch(self, request: Request, call_next) -> Response:
        # Permitir preflight CORS
        if request.method == "OPTIONS":
            return await call_next(request)

        # Generar request ID único
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Obtener IP del cliente
        client_ip = self._get_client_ip(request)
        request.state.client_ip = client_ip
        
        # Verificar rate limiting
        if not self._check_rate_limit(client_ip):
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": "Rate limit exceeded",
                    "request_id": request_id
                }
            )
        
        # Validar headers de seguridad
        if not self._validate_security_headers(request):
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "detail": "Invalid security headers",
                    "request_id": request_id
                }
            )
        
        # Procesar request
        start_time = time.time()
        response = await call_next(request)
        duration = time.time() - start_time
        
        # Agregar headers de seguridad
        self._add_security_headers(response)
        
        # Log de la request
        self._log_request(request, response, duration, request_id)
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """Obtener IP real del cliente"""
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        return request.client.host if request.client else "unknown"
    
    def _check_rate_limit(self, client_ip: str) -> bool:
        """Verificar rate limiting por IP"""
        current_time = time.time()
        
        # Implementación simple en memoria (en producción usar Redis)
        if not hasattr(self, '_rate_limit_store'):
            self._rate_limit_store: Dict[str, List[float]] = {}
        
        if client_ip not in self._rate_limit_store:
            self._rate_limit_store[client_ip] = []
        
        # Limpiar requests antiguos
        self._rate_limit_store[client_ip] = [
            req_time for req_time in self._rate_limit_store[client_ip]
            if current_time - req_time < self.rate_limit_window
        ]
        
        # Verificar si puede hacer la request
        if len(self._rate_limit_store[client_ip]) >= self.rate_limit_requests:
            return False
        
        # Agregar request actual
        self._rate_limit_store[client_ip].append(current_time)
        return True
    
    def _validate_security_headers(self, request: Request) -> bool:
        user_agent = request.headers.get("User-Agent", "")
        if not user_agent or len(user_agent) < 5:
            print(f"[SECURITY] User-Agent inválido: '{user_agent}'")
            return False

        if request.method in ["POST", "PUT", "PATCH"]:
            content_type = request.headers.get("Content-Type", "")
            # Permitir application/json o multipart/form-data
            if not content_type or (("application/json" not in content_type) and ("multipart/form-data" not in content_type)):
                print(f"[SECURITY] Content-Type inválido: '{content_type}'")
                return False

        return True

    
    def _add_security_headers(self, response: Response):
        """Agregar headers de seguridad a la respuesta"""
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline';"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        response.headers["X-Request-ID"] = getattr(response, 'request_id', 'unknown')
    
    def _log_request(self, request: Request, response: Response, duration: float, request_id: str):
        """Log de la request para monitoreo"""
        try:
            from core.logger import log_request
            user_id = getattr(request.state, 'user_id', None)
            log_request(
                request_id=request_id,
                method=request.method,
                url=str(request.url),
                status_code=response.status_code,
                user_id=user_id,
                duration=duration
            )
        except ImportError:
            # Fallback si no está disponible el logger
            pass

def setup_cors_middleware(app):
    """Configurar CORS de forma segura"""
    allowed_origins_env = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:3002")
    allowed_origins = [origin.strip() for origin in allowed_origins_env.split(",") if origin.strip()]
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID"]
    )

def setup_security_middleware(app):
    """Configurar middleware de seguridad"""
    app.add_middleware(SecurityMiddleware)
    
    # Configurar rate limiter global
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler) 