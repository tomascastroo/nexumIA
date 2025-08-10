"""
Tests para el middleware de rate limiting.
Verifica que el rate limiter devuelve 429 al exceder el límite.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import time
from unittest.mock import patch, Mock, MagicMock
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

# Configurar variables de entorno para tests ANTES de importar el módulo
os.environ["DISABLE_RATE_LIMITER"] = "false"
os.environ["RATE_LIMIT_MAX"] = "5"
os.environ["RATE_LIMIT_WINDOW"] = "60"

from middleware.rate_limit import (
    rate_limit_middleware,
    get_client_ip,
    generate_rate_limit_key,
    get_rate_limit_info,
    RATE_LIMIT_MAX,
    RATE_LIMIT_WINDOW
)

@pytest.fixture
def app():
    """Crear aplicación FastAPI para testing."""
    app = FastAPI()
    
    @app.get("/test")
    async def test_endpoint():
        return {"message": "test"}
    
    @app.get("/test2")
    async def test_endpoint2():
        return {"message": "test2"}
    
    # Aplicar middleware de rate limiting
    app.middleware("http")(rate_limit_middleware)
    
    return app

@pytest.fixture
def client(app):
    """Cliente de test para la aplicación."""
    return TestClient(app)

@pytest.fixture
def mock_redis():
    """Mock de Redis para testing."""
    with patch('middleware.rate_limit.get_redis_client') as mock_get_redis:
        mock_redis_client = Mock()
        mock_redis_client.get.return_value = "0"
        mock_redis_client.pipeline.return_value = Mock()
        mock_get_redis.return_value = mock_redis_client
        yield mock_redis_client

class TestRateLimiting:
    """Tests para el middleware de rate limiting."""
    
    def test_get_client_ip_direct(self):
        """Test obtener IP directa del cliente."""
        request = Mock()
        request.headers = {}
        request.client.host = "192.168.1.1"
        
        ip = get_client_ip(request)
        assert ip == "192.168.1.1"
    
    def test_get_client_ip_forwarded_for(self):
        """Test obtener IP desde X-Forwarded-For."""
        request = Mock()
        request.headers = {"X-Forwarded-For": "10.0.0.1, 192.168.1.1"}
        request.client.host = "192.168.1.1"
        
        ip = get_client_ip(request)
        assert ip == "10.0.0.1"
    
    def test_get_client_ip_real_ip(self):
        """Test obtener IP desde X-Real-IP."""
        request = Mock()
        request.headers = {"X-Real-IP": "10.0.0.2"}
        request.client.host = "192.168.1.1"
        
        ip = get_client_ip(request)
        assert ip == "10.0.0.2"
    
    def test_generate_rate_limit_key(self):
        """Test generar clave de rate limiting."""
        ip = "192.168.1.1"
        endpoint = "/test"
        
        key = generate_rate_limit_key(ip, endpoint)
        
        assert key.startswith("rate_limit:")
        assert len(key) > 20  # Debe ser un hash MD5
    
    def test_rate_limit_info(self, mock_redis):
        """Test obtener información de rate limiting."""
        mock_redis.get.return_value = "3"
        
        info = get_rate_limit_info("192.168.1.1", "/test")
        
        assert info["ip"] == "192.168.1.1"
        assert info["endpoint"] == "/test"
        assert info["current_requests"] == 3
        assert info["limit"] == 5
        assert info["remaining"] == 2
    
    def test_rate_limit_info_redis_unavailable(self):
        """Test cuando Redis no está disponible."""
        with patch('middleware.rate_limit.get_redis_client', return_value=None):
            info = get_rate_limit_info("192.168.1.1", "/test")
            assert info["error"] == "Redis no disponible"
    
    @patch('middleware.rate_limit.get_redis_client')
    def test_rate_limit_middleware_success(self, mock_get_redis, client):
        """Test que el middleware permite peticiones dentro del límite."""
        # Mock Redis
        mock_redis = Mock()
        mock_redis.get.return_value = "2"  # 2 peticiones previas
        mock_pipeline = Mock()
        mock_pipeline.incr.return_value = mock_pipeline
        mock_pipeline.expire.return_value = mock_pipeline
        mock_pipeline.execute.return_value = [3]  # incr retorna 3
        mock_redis.pipeline.return_value = mock_pipeline
        mock_get_redis.return_value = mock_redis
        
        # Hacer petición
        response = client.get("/test")
        
        assert response.status_code == 200
        assert response.json() == {"message": "test"}
        
        # Verificar headers de rate limiting
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers
        assert "X-RateLimit-Reset" in response.headers
    
    @patch('middleware.rate_limit.get_redis_client')
    def test_rate_limit_middleware_exceeded(self, mock_get_redis, client):
        """Test que el middleware devuelve 429 cuando se excede el límite."""
        # Mock Redis con límite excedido
        mock_redis = Mock()
        mock_redis.get.return_value = "5"  # Límite alcanzado
        mock_get_redis.return_value = mock_redis
        
        # Hacer petición
        response = client.get("/test")
        
        assert response.status_code == 429
        assert response.json()["error"] == "Rate limit exceeded"
        assert "Too many requests" in response.json()["message"]
        assert "Retry-After" in response.headers
    
    @patch('middleware.rate_limit.get_redis_client')
    def test_rate_limit_middleware_redis_unavailable(self, mock_get_redis, client):
        """Test que el middleware funciona cuando Redis no está disponible."""
        # Mock Redis no disponible
        mock_get_redis.return_value = None
        
        # Hacer petición
        response = client.get("/test")
        
        assert response.status_code == 200
        assert response.json() == {"message": "test"}
    
    @patch('middleware.rate_limit.get_redis_client')
    def test_rate_limit_middleware_redis_error(self, mock_get_redis, client):
        """Test que el middleware maneja errores de Redis."""
        # Mock Redis con error
        mock_redis = Mock()
        mock_redis.get.side_effect = Exception("Redis error")
        mock_get_redis.return_value = mock_redis
        
        # Hacer petición
        response = client.get("/test")
        
        assert response.status_code == 200
        assert response.json() == {"message": "test"}
    
    @patch('middleware.rate_limit.get_redis_client')
    def test_rate_limit_different_endpoints(self, mock_get_redis, client):
        """Test que el rate limiting es independiente por endpoint."""
        # Mock Redis
        mock_redis = Mock()
        mock_redis.get.return_value = "4"  # Casi al límite
        mock_pipeline = Mock()
        mock_pipeline.incr.return_value = mock_pipeline
        mock_pipeline.expire.return_value = mock_pipeline
        mock_pipeline.execute.return_value = [5]
        mock_redis.pipeline.return_value = mock_pipeline
        mock_get_redis.return_value = mock_redis
        
        # Hacer peticiones a diferentes endpoints
        response1 = client.get("/test")
        response2 = client.get("/test2")
        
        # Ambas deben funcionar porque son endpoints diferentes
        assert response1.status_code == 200
        assert response2.status_code == 200
    
    @patch('middleware.rate_limit.get_redis_client')
    def test_rate_limit_headers_correct(self, mock_get_redis, client):
        """Test que los headers de rate limiting son correctos."""
        # Mock Redis
        mock_redis = Mock()
        mock_redis.get.return_value = "1"
        mock_pipeline = Mock()
        mock_pipeline.incr.return_value = mock_pipeline
        mock_pipeline.expire.return_value = mock_pipeline
        mock_pipeline.execute.return_value = [2]  # incr retorna 2
        mock_redis.pipeline.return_value = mock_pipeline
        mock_get_redis.return_value = mock_redis
        
        # Hacer petición
        response = client.get("/test")
        
        # Verificar headers
        assert response.headers["X-RateLimit-Limit"] == "5"
        assert response.headers["X-RateLimit-Remaining"] == "3"  # 5 - 2 = 3
        assert "X-RateLimit-Reset" in response.headers
    
    def test_rate_limit_configuration(self):
        """Test que la configuración se lee correctamente de variables de entorno."""
        # Verificar que las variables se leen correctamente
        assert RATE_LIMIT_MAX == 5
        assert RATE_LIMIT_WINDOW == 60
    
    @patch('middleware.rate_limit.get_redis_client')
    def test_rate_limit_pipeline_usage(self, mock_get_redis, client):
        """Test que se usa pipeline de Redis para atomicidad."""
        # Mock Redis
        mock_redis = Mock()
        mock_redis.get.return_value = "0"
        mock_pipeline = Mock()
        mock_pipeline.incr.return_value = mock_pipeline
        mock_pipeline.expire.return_value = mock_pipeline
        mock_pipeline.execute.return_value = [1]  # incr retorna 1
        mock_redis.pipeline.return_value = mock_pipeline
        mock_get_redis.return_value = mock_redis
        
        # Hacer petición
        response = client.get("/test")
        
        # Verificar que se usó pipeline
        mock_redis.pipeline.assert_called_once()
        mock_pipeline.incr.assert_called_once()
        mock_pipeline.expire.assert_called_once()
        mock_pipeline.execute.assert_called_once()
        
        assert response.status_code == 200

class TestRateLimitIntegration:
    """Tests de integración para rate limiting."""
    
    @patch('middleware.rate_limit.get_redis_client')
    def test_multiple_requests_same_ip(self, mock_get_redis, client):
        """Test múltiples peticiones desde la misma IP."""
        # Mock Redis
        mock_redis = Mock()
        mock_redis.get.side_effect = ["0", "1", "2", "3", "4", "5"]  # Incrementando
        mock_pipeline = Mock()
        mock_pipeline.incr.return_value = mock_pipeline
        mock_pipeline.expire.return_value = mock_pipeline
        mock_pipeline.execute.return_value = [1, 2, 3, 4, 5, 6]
        mock_redis.pipeline.return_value = mock_pipeline
        mock_get_redis.return_value = mock_redis
        
        # Hacer 6 peticiones (la última debe fallar)
        responses = []
        for i in range(6):
            response = client.get("/test")
            responses.append(response)
        
        # Las primeras 5 deben ser exitosas
        for i in range(5):
            assert responses[i].status_code == 200
        
        # La última debe fallar
        assert responses[5].status_code == 429
    
    @patch('middleware.rate_limit.get_redis_client')
    def test_rate_limit_reset_after_window(self, mock_get_redis, client):
        """Test que el rate limit se resetea después de la ventana de tiempo."""
        # Mock Redis que simula paso del tiempo
        mock_redis = Mock()
        mock_redis.get.side_effect = ["5", "0"]  # Primero al límite, luego reseteado
        mock_pipeline = Mock()
        mock_pipeline.incr.return_value = mock_pipeline
        mock_pipeline.expire.return_value = mock_pipeline
        mock_pipeline.execute.return_value = [6, 1]
        mock_redis.pipeline.return_value = mock_pipeline
        mock_get_redis.return_value = mock_redis
        
        # Primera petición debe fallar
        response1 = client.get("/test")
        assert response1.status_code == 429
        
        # Segunda petición debe funcionar (simulando reset)
        response2 = client.get("/test")
        assert response2.status_code == 200 