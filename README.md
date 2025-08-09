# 🚀 Nexum IA - Sistema de Gestión Inteligente de Cobranzas

Sistema completo de gestión de deudores con IA, construido con FastAPI, React y PostgreSQL. Incluye clasificación automática de estados emocionales, estrategias de cobranza inteligentes y dashboards en tiempo real.

## 🎯 **Características Principales**

- 🤖 **IA Conversacional**: Clasificación automática de estados emocionales
- 📊 **Dashboards Interactivos**: Métricas en tiempo real con gráficos
- 🎯 **Estrategias Inteligentes**: Reglas de cobranza automatizadas
- 💳 **Integración de Pagos**: Links de pago automáticos
- 📱 **WhatsApp Integration**: Comunicación directa con deudores
- 🔒 **Seguridad Empresarial**: JWT, rate limiting, headers de seguridad
- 📈 **Escalabilidad**: Connection pooling, caching, procesamiento asíncrono

## 🏗️ **Arquitectura**

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │────│   FastAPI       │────│   PostgreSQL    │
│   React + TS    │    │   Backend       │    │   Database      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   Redis Cache   │
                       │   + Celery      │
                       └─────────────────┘
```

## 🚀 **Quick Start**

### **Prerrequisitos**
- Python 3.11+
- Node.js 16+
- PostgreSQL 12+
- Redis (opcional para cache)

### **1. Clonar Repositorio**
```bash
git clone https://github.com/tu-usuario/nexum-ia.git
cd nexum-ia
```

### **2. Configurar Backend**
```bash
# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno (nunca subir secretos al repo)
cp env.example .env  # o .env.example
# Editar .env con tus configuraciones (SECRET_KEY, DATABASE_URL, OPENAI_API_KEY, Twilio, etc.)

# Configurar base de datos
python init_db.py

# Ejecutar migraciones (si aplica)
alembic upgrade head || echo "Migrations no configuradas aún"

# Crear índices para producción (opcional)
psql "$DATABASE_URL" -f scripts/create_indexes.sql || true
```

### **3. Configurar Frontend**
```bash
cd frontend
npm install
npm start
```

### **4. Ejecutar Backend**
```bash
# Desarrollo
uvicorn main:app --reload

# Producción (Gunicorn + Uvicorn)
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## 🔐 **Configuración de Seguridad**

### **Variables de Entorno Críticas**
```bash
# Generar claves seguras
SECRET_KEY=$(openssl rand -hex 32)
JWT_ALG=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000

# Configurar en .env (ejemplo)
SECRET_KEY=tu_secret_key_generado
OPENAI_API_KEY=
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/nexum
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886
REDIS_URL=redis://localhost:6379/0
```

### **Headers de Seguridad Implementados**
- ✅ Strict-Transport-Security
- ✅ Content-Security-Policy
- ✅ X-Frame-Options
- ✅ X-Content-Type-Options
- ✅ Rate Limiting (100 req/min por IP)

## 📊 **Monitoreo y Métricas**

### **Endpoints de Monitoreo**
- `GET /health` - Health check
- `GET /metrics` - Métricas Prometheus (expuesto por `core/metrics.py`)
- `GET /docs` - Documentación API

### **Logging Estructurado**
```bash
# Ver logs en tiempo real
tail -f logs/app.log

# Logs en formato JSON para producción
# Integración con ELK Stack, Datadog, etc.
```

### **Métricas Disponibles**
- 📈 Requests HTTP (total, duración, códigos)
- 💰 Pagos procesados (cantidad, estado)
- 🤖 Requests a IA (tiempo, éxito)
- 🔒 Eventos de seguridad
- 🗄️ Conexiones de base de datos

## 🗄️ **Base de Datos**

### **Índices Críticos Implementados**
```sql
-- Índices automáticos para performance
CREATE INDEX idx_debtors_state ON debtors(state);
CREATE INDEX idx_debtors_dni ON debtors(dni);
CREATE INDEX idx_debtors_phone ON debtors(phone);
CREATE INDEX idx_payments_status ON debt_payments(status);
-- ... y más índices optimizados
```

### **Backups Automáticos**
```bash
# Configurar backup diario
crontab -e
# Agregar: 0 2 * * * /ruta/scripts/backup_database.sh
```

## 🚀 **Deployment en Producción**

### **1. Configurar Servidor**
```bash
# Instalar dependencias del sistema
sudo apt update
sudo apt install postgresql redis-server nginx

# Configurar PostgreSQL
sudo -u postgres createuser nexum_user
sudo -u postgres createdb nexum_ia -O nexum_user
```

### **2. Configurar Nginx**
```nginx
# /etc/nginx/sites-available/nexum_ia
server {
    listen 443 ssl http2;
    server_name api.tu-dominio.com;
    
    # SSL y headers de seguridad
    ssl_certificate /etc/letsencrypt/live/api.tu-dominio.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.tu-dominio.com/privkey.pem;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### **3. Systemd Service**
```ini
# /etc/systemd/system/nexum_ia.service
[Unit]
Description=Nexum IA API
After=network.target

[Service]
Type=exec
User=nexum
WorkingDirectory=/opt/nexum_ia
ExecStart=/opt/nexum_ia/venv/bin/gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
Restart=always

[Install]
WantedBy=multi-user.target
```

## 📋 **Checklist de Producción**

### **Antes del Deploy**
- [ ] Variables de entorno configuradas
- [ ] Base de datos migrada y con índices
- [ ] Logs configurados
- [ ] Métricas habilitadas
- [ ] Backups configurados
- [ ] SSL/TLS configurado
- [ ] Rate limiting configurado
- [ ] CORS configurado

### **Después del Deploy**
- [ ] Health check pasa (`/health`)
- [ ] Métricas disponibles (`/metrics`)
- [ ] Logs se generan
- [ ] Backups funcionan
- [ ] Alertas configuradas
- [ ] Performance aceptable
- [ ] Seguridad verificada

## 🔧 **Mantenimiento**

### **Tareas Diarias**
```bash
# Verificar logs
tail -f logs/app.log

# Verificar health check
curl http://localhost:8000/health

# Verificar backups
ls -la /var/backups/nexum_ia/
```

### **Tareas Semanales**
```bash
# Análisis de performance
psql -d nexum_ia -c "SELECT query, mean_time FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;"

# Limpieza de logs
find logs/ -name "*.log" -mtime +30 -delete
```

## 🚨 **Troubleshooting**

### **Problemas Comunes**

#### **Base de Datos No Conecta**
```bash
# Verificar servicio
sudo systemctl status postgresql

# Verificar conexión
psql -h localhost -U nexum_user -d nexum_ia
```

#### **Rate Limiting Muy Restrictivo**
```bash
# Ajustar en .env
API_RATE_LIMIT=200
API_RATE_LIMIT_WINDOW=60
```

#### **Logs No Se Generan**
```bash
# Verificar permisos
ls -la logs/

# Verificar configuración
echo $LOG_LEVEL
echo $ENVIRONMENT
```

## 📚 **Documentación Adicional**

- [📖 Documentación de Infraestructura](docs/infra.md)
- [🔧 Guía de Mantenimiento](docs/maintenance.md)
- [🚀 Guía de Deployment](docs/deployment.md)
- [📊 Guía de Monitoreo](docs/monitoring.md)

## 🤝 **Contribución**

1. Fork el proyecto
2. Crear feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit cambios (`git commit -m 'Add AmazingFeature'`)
4. Push al branch (`git push origin feature/AmazingFeature`)
5. Abrir Pull Request

## 📄 **Licencia**

Este proyecto está bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para detalles.

## 📞 **Soporte**

- **Email**: soporte@tu-dominio.com
- **Documentación**: https://docs.tu-dominio.com
- **Issues**: https://github.com/tu-usuario/nexum-ia/issues

---

## 🎉 **¡Listo para Producción!**

El sistema está configurado con todas las mejores prácticas de seguridad, escalabilidad y monitoreo. Sigue la documentación de infraestructura para un deployment exitoso en producción.

**¡Tu sistema de cobranzas inteligente está listo para escalar! 🚀** 

# Nexum IA – Checklist de Producción

## 🚦 Verificación final
- [x] Variables de entorno en `.env`
- [x] Redis y Celery corriendo
- [x] Endpoints críticos cacheados
- [x] Tareas asíncronas Celery funcionando
- [x] Métricas Prometheus expuestas en `/metrics`
- [x] Tests automatizados y de performance

## 🧪 Testing y CI
```bash
pytest --cov=services --cov=routers
```

CI (GitHub Actions): `.github/workflows/ci.yml` corre lint (ruff), type-check (mypy), y tests con Postgres + Redis de servicios.

Endpoints críticos cubiertos:
- Auth: registro, login, whoami, guard de admin.
- Webhook: backpressure (respuesta rápida, encolar tarea Celery).
- WhatsApp: uso de variables de entorno y cliente mockeado.
```

## 🚀 Performance
```bash
locust -f tests/perf_test_locust.py --host=http://localhost:8000
```

## 🔄 Tareas Celery (Backpressure)
- Enviar WhatsApp: `POST /whatsapp/send`
- Analizar deudores: `POST /debtors/analyze`
- Guardar conversación IA: `POST /debtors/conversation`
- Analizar estrategias: `POST /strategies/analyze`
- Consultar estado: `GET /task_status/{task_id}`

Webhook Twilio encola `process_incoming_message(phone, body)` para no bloquear el request.

## 📊 Monitoreo
- Prometheus: `/metrics`
- Flower: `flower -A tasks.celery_app --port=5555`

## 🛠 Troubleshooting
- Verifica Redis y Celery activos
- Usa `/metrics` para monitoreo
- Logs estructurados en `logs/` 

## 🚀 Levantar todo el stack con Docker Compose

1. Instala [Docker Desktop](https://www.docker.com/products/docker-desktop/) y ábrelo.
2. Copia tus variables de entorno desde `env.example` a `.env` si es necesario.
3. Ejecuta:

```bash
docker-compose up --build
```

Esto levantará backend, frontend, base de datos, Redis, Celery, Flower, Prometheus y Grafana.

- Backend: http://localhost:8000
- Frontend: http://localhost:3000
- Flower: http://localhost:5555
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3001 