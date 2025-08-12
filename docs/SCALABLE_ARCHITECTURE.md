# Nexum IA – Arquitectura Escalable

## 1. Caching con Redis
- **Servicio:** `services/cache_service.py`
- **Endpoints cacheados:** `/debtors`, `/campaigns`, `/strategies`, respuestas IA
- **Librerías:** aioredis, prometheus_client
- **Comandos verificación:**
  - `redis-cli monitor` para ver actividad
  - `/metrics` para ver hits/miss

## 2. Procesamiento Asíncrono con Celery
- **Carpeta:** `tasks/`
- **Workers:** WhatsApp, IA, análisis masivo
- **Librerías:** celery[redis], flower, structlog
- **Comandos:**
  - `celery -A tasks.celery_app worker --loglevel=info`
  - `flower -A tasks.celery_app --port=5555`

## 3. Testing
- **Librerías:** pytest, pytest-cov, locust
- **Cobertura:** `pytest --cov=services --cov=routers`
- **Performance:** `locust -f tests/perf_test.py`

## 4. Métricas y Monitoreo
- **Prometheus:** `/metrics` endpoint
- **Grafana:** dashboards custom

## 5. Logging
- **Librerías:** loguru, structlog
- **Formato:** JSON estructurado

---

## Rutas afectadas
- `/debtors` (GET, POST, PUT, DELETE)
- `/campaigns` (GET, POST, PUT, DELETE)
- `/strategies` (GET, POST, PUT, DELETE)
- `/openai/ask` (POST)

---

## Comandos útiles
- `pytest --cov`
- `celery -A tasks.celery_app worker --loglevel=info`
- `flower -A tasks.celery_app --port=5555`
- `locust -f tests/perf_test.py`
- `curl http://localhost:8000/metrics`

---

## Troubleshooting
- Verifica Redis y Celery corriendo
- Usa `/metrics` para monitoreo
- Logs estructurados en `logs/` 