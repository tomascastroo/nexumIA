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

## 🔐 Variables de Entorno (ejemplo)
```env
SECRET_KEY=...
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/nexum
REDIS_URL=redis://localhost:6379/0
OPENAI_API_KEY=sk-...
TWILIO_ACCOUNT_SID=...
TWILIO_AUTH_TOKEN=...
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886
RATE_LIMIT_MAX=100
RATE_LIMIT_WINDOW=3600
DISABLE_RATE_LIMITER=false
```

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