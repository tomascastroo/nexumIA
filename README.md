# 🚀 Nexum IA - Sistema de Gestión Inteligente de Cobranzas

Sistema completo de gestión de deudores con IA, construido con FastAPI, React y PostgreSQL. Incluye clasificación automática de estados emocionales, estrategias de cobranza inteligentes y dashboards en tiempo real.

## 🎯 Características Principales
- 🤖 IA Conversacional (Celery + reintentos)
- 📊 Dashboards y KPIs
- 🎯 Estrategias por reglas avanzadas
- 💳 Links de pago
- 📱 WhatsApp
- 🔒 Seguridad: JWT, rate limiting, headers
- ⚙️ Escalabilidad: Redis, Celery, pooling

## 🏗️ Arquitectura
```
Frontend (React)
  │
API FastAPI ─ Redis (limiter)
  │
Celery (OpenAI, backpressure) ─ Redis (broker/result)
  │
PostgreSQL
```

## 🚀 Quick Start

### Prerrequisitos
- Python 3.11+
- Node.js 18+
- PostgreSQL 12+
- Redis 6+

### 1) Backend
```bash
pip install -r requirements.txt
cp env.example .env
# Edita .env con SECRET_KEY, DATABASE_URL, REDIS_URL, OPENAI_API_KEY, TWILIO_*
python init_db.py
alembic upgrade head || true
```

### 2) Frontend
```bash
cd frontend
npm install
# API base
export REACT_APP_API_URL=http://localhost:8000
npm start
```

### 3) Backend (dev)
```bash
uvicorn main:app --reload
```

### 4) Celery + Redis
```bash
# Broker y result backend usan REDIS_URL
celery -A tasks.celery_app worker -l info
# Opcional: Flower
flower -A tasks.celery_app --port=5555
```

## 🧪 Verificación (verify.sh)
```bash
chmod +x verify.sh
./verify.sh
```
Hace: búsqueda de secretos, black/isort/flake8/mypy (si instalados), compila Python, corre tests, valida .gitignore.

## 🛡️ Pre-commit hooks

Para asegurar calidad y seguridad automática antes de cada commit:

```bash
pip install pre-commit
pre-commit install
# Para correr manualmente en todos los archivos:
pre-commit run --all-files
```

Incluye: ruff, isort, black, bandit, end-of-file-fixer.

## 🔑 Tabla de variables de entorno

| Variable                  | Descripción                        | Ejemplo/Valor dummy                  |
|---------------------------|------------------------------------|--------------------------------------|
| SECRET_KEY                | Clave secreta JWT                  | CHANGE_ME                            |
| JWT_ALG                   | Algoritmo JWT                      | HS256                                |
| ACCESS_TOKEN_EXPIRE_MINUTES | Expiración token (min)           | 60                                   |
| API_RATE_LIMIT            | Límite de requests                 | 100                                  |
| API_RATE_LIMIT_WINDOW     | Ventana de rate limit (seg)        | 60                                   |
| ALLOWED_ORIGINS           | Orígenes permitidos CORS           | https://app.midominio.com            |
| REDIS_URL                 | URL de Redis                       | redis://redis:6379/0                 |
| REDIS_HOST                | Host Redis                         | redis                                |
| REDIS_PORT                | Puerto Redis                       | 6379                                 |
| REDIS_DB                  | DB Redis                           | 0                                    |
| LOG_LEVEL                 | Nivel de log                       | INFO                                 |
| APP_ENV                   | Entorno app                        | development                          |
| DATABASE_URL              | URL base de datos                  | postgresql://postgres:postgres@localhost:5432/nexum |
| OPENAI_API_KEY            | API key OpenAI (dummy en dev)      | dummy                                |
| TWILIO_ACCOUNT_SID        | SID Twilio (dummy en dev)          | dummy                                |
| TWILIO_AUTH_TOKEN         | Token Twilio (dummy en dev)        | dummy                                |
| TWILIO_WHATSAPP_NUMBER    | WhatsApp sender (dummy en dev)     | whatsapp:+14155238886                |

## 🧭 Frontend (React CRA)
- Autenticación: `authFetch` añade `Authorization` y maneja 401 / expiración
- Config API: `REACT_APP_API_URL`
- Carga CSV: preview + validación de columnas `phone` y `state`
- Historial/Analíticas: `StrategyTraceability` via `/traceability`

## 🐳 Docker Compose (stack completo)
```bash
docker-compose up --build
# Backend: http://localhost:8000
# Frontend: http://localhost:3000
# Flower:   http://localhost:5555
# Prometheus: http://localhost:9090
```

## 📚 Documentación
- LICENSE (MIT)
- CODE_OF_CONDUCT.md
- CONTRIBUTING.md
- SECURITY.md (reporte de vulnerabilidades)
- CHANGELOG.md (Conventional Commits)

## 🤝 Contribución
- Convenciones: Conventional Commits
- Ejecuta `./verify.sh` antes de PR
- Plantillas de issues/PR (si faltan, se incorporarán en `.github/`)

## 🗺️ Backlog (futuro)
- Multicanal (email/SMS/WhatsApp)
- Motor predictivo (propensión a pago)
- Integraciones CRM/ERP
- Multi-tenant

Ver Issues con etiquetas `enhancement` y `roadmap` con criterios de aceptación. 