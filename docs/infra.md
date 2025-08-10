# 📚 Documentación de Infraestructura - Nexum IA

## 🎯 **Objetivo**
Esta documentación describe la configuración de infraestructura necesaria para desplegar el sistema Nexum IA en producción de forma segura y escalable.

---

## 🔐 **SEGURIDAD**

### **Variables de Entorno**
El sistema utiliza variables de entorno para todas las configuraciones sensibles. Copia `env.example` a `.env` y configura:

```bash
# Copiar archivo de ejemplo
cp env.example .env

# Editar con valores reales
nano .env
```

### **Configuraciones Críticas de Seguridad**

#### **1. Claves de Encriptación**
```bash
# Generar SECRET_KEY (mínimo 32 caracteres)
SECRET_KEY=$(openssl rand -hex 32)

# Generar ENCRYPTION_KEY (32 bytes)
ENCRYPTION_KEY=$(openssl rand -base64 32)
```

#### **2. Rate Limiting**
```bash
# Requests por minuto por IP
API_RATE_LIMIT=100
API_RATE_LIMIT_WINDOW=60
```

#### **3. CORS Restrictivo**
```bash
# Solo orígenes permitidos
ALLOWED_ORIGINS=https://tu-dominio.com,https://app.tu-dominio.com
```

### **Headers de Seguridad Implementados**
- `Strict-Transport-Security`: Fuerza HTTPS
- `Content-Security-Policy`: Previene XSS
- `X-Frame-Options`: Previene clickjacking
- `X-Content-Type-Options`: Previene MIME sniffing
- `Referrer-Policy`: Controla información de referrer

---

## 🗄️ **BASE DE DATOS**

### **Configuración de PostgreSQL**

#### **1. Instalación y Configuración**
```bash
# Instalar PostgreSQL
sudo apt update
sudo apt install postgresql postgresql-contrib

# Crear usuario y base de datos
sudo -u postgres psql
CREATE USER nexum_user WITH PASSWORD 'tu_password_seguro';
CREATE DATABASE nexum_ia OWNER nexum_user;
GRANT ALL PRIVILEGES ON DATABASE nexum_ia TO nexum_user;
\q
```

#### **2. Connection Pooling**
```bash
# Configurar en .env
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=30
DB_POOL_RECYCLE=3600
```

#### **3. Índices Críticos**
```bash
# Ejecutar script de índices
psql -d nexum_ia -U nexum_user -f scripts/create_indexes.sql
```

### **Backups Automáticos**

#### **1. Configurar Cron Job**
```bash
# Editar crontab
crontab -e

# Agregar backup diario a las 2 AM
0 2 * * * /ruta/completa/scripts/backup_database.sh
```

#### **2. Verificar Backups**
```bash
# Listar backups
ls -la /var/backups/nexum_ia/

# Verificar integridad
gunzip -t /var/backups/nexum_ia/nexum_ia_backup_YYYYMMDD_HHMMSS.sql.gz
```

---

## 📊 **MONITOREO**

### **Logging Estructurado**

#### **1. Configuración**
```bash
# Nivel de logging
LOG_LEVEL=INFO

# Habilitar métricas
ENABLE_METRICS=true
```

#### **2. Rotación de Logs**
Los logs se rotan automáticamente:
- Tamaño máximo: 100MB
- Retención: 30 días
- Compresión: ZIP

#### **3. Formato de Logs**
En producción, los logs se generan en formato JSON para integración con:
- ELK Stack
- Datadog
- Logtail
- CloudWatch

### **Métricas de Prometheus**

#### **1. Endpoint de Métricas**
```
GET /metrics
```

#### **2. Métricas Disponibles**
- **HTTP**: Requests totales, duración, códigos de estado
- **Negocio**: Deudores, campañas, pagos
- **IA**: Requests a OpenAI, tiempo de respuesta
- **Sistema**: Conexiones DB, Redis
- **Seguridad**: Eventos de seguridad, rate limiting

#### **3. Configurar Prometheus**
```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'nexum_ia'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
    scrape_interval: 15s
```

### **Alertas Críticas**

#### **1. Configurar Alertas**
```bash
# Variables de entorno para alertas
ALERT_EMAIL=admin@tu-dominio.com
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
```

#### **2. Alertas Implementadas**
- **Errores 500**: > 5% de requests
- **DB inactiva**: Sin conexiones por 5 minutos
- **Rate limit**: > 100 violaciones por hora
- **Backup fallido**: Último backup > 24 horas

---

## 🚀 **DEPLOYMENT**

### **Configuración de Producción**

#### **1. Instalar Dependencias**
```bash
# Instalar Python dependencies
pip install -r requirements.txt

# Verificar instalación
python -c "import fastapi, sqlalchemy, prometheus_client"
```

#### **2. Configurar Base de Datos**
```bash
# Ejecutar migraciones
alembic upgrade head

# Crear índices
psql -d nexum_ia -f scripts/create_indexes.sql
```

#### **3. Configurar Logs**
```bash
# Crear directorio de logs
mkdir -p logs
chmod 755 logs
```

### **Servidor de Producción**

#### **1. Usando Uvicorn**
```bash
# Comando de inicio
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

#### **2. Usando Gunicorn (Recomendado)**
```bash
# Instalar gunicorn
pip install gunicorn

# Comando de inicio
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

#### **3. Systemd Service**
```ini
# /etc/systemd/system/nexum_ia.service
[Unit]
Description=Nexum IA API
After=network.target

[Service]
Type=exec
User=nexum
WorkingDirectory=/opt/nexum_ia
Environment=PATH=/opt/nexum_ia/venv/bin
ExecStart=/opt/nexum_ia/venv/bin/gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### **Nginx como Reverse Proxy**

#### **1. Configuración Nginx**
```nginx
# /etc/nginx/sites-available/nexum_ia
server {
    listen 80;
    server_name api.tu-dominio.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.tu-dominio.com;

    ssl_certificate /etc/letsencrypt/live/api.tu-dominio.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.tu-dominio.com/privkey.pem;

    # Headers de seguridad
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options DENY always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-XSS-Protection "1; mode=block" always;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Rate limiting
        limit_req_zone $binary_remote_addr zone=api:10m rate=100r/m;
        limit_req zone=api burst=200 nodelay;
    }

    location /metrics {
        # Solo permitir acceso desde Prometheus
        allow 127.0.0.1;
        deny all;
        proxy_pass http://127.0.0.1:8000;
    }
}
```

#### **2. Habilitar Sitio**
```bash
# Crear enlace simbólico
sudo ln -s /etc/nginx/sites-available/nexum_ia /etc/nginx/sites-enabled/

# Verificar configuración
sudo nginx -t

# Recargar Nginx
sudo systemctl reload nginx
```

---

## 🔧 **MANTENIMIENTO**

### **Tareas Diarias**

#### **1. Verificar Logs**
```bash
# Verificar logs de aplicación
tail -f logs/app.log

# Verificar logs de backup
tail -f /var/backups/nexum_ia/backup.log
```

#### **2. Verificar Métricas**
```bash
# Verificar endpoint de métricas
curl http://localhost:8000/metrics

# Verificar health check
curl http://localhost:8000/health
```

#### **3. Verificar Backups**
```bash
# Listar backups recientes
ls -la /var/backups/nexum_ia/ | head -10

# Verificar integridad del último backup
gunzip -t /var/backups/nexum_ia/$(ls -t /var/backups/nexum_ia/*.gz | head -1)
```

### **Tareas Semanales**

#### **1. Análisis de Performance**
```sql
-- Verificar queries lentas
SELECT query, mean_time, calls 
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;
```

#### **2. Limpieza de Logs**
```bash
# Limpiar logs antiguos (más de 30 días)
find logs/ -name "*.log" -mtime +30 -delete
```

#### **3. Verificar Espacio en Disco**
```bash
# Verificar uso de disco
df -h

# Verificar tamaño de base de datos
psql -d nexum_ia -c "SELECT pg_size_pretty(pg_database_size('nexum_ia'));"
```

### **Tareas Mensuales**

#### **1. Actualización de Dependencias**
```bash
# Verificar dependencias desactualizadas
pip list --outdated

# Actualizar dependencias críticas
pip install --upgrade fastapi uvicorn sqlalchemy
```

#### **2. Revisión de Seguridad**
```bash
# Verificar logs de seguridad
grep "security" logs/app.log | tail -50

# Verificar intentos de acceso fallidos
grep "401\|403" logs/app.log | tail -50
```

#### **3. Análisis de Métricas**
```bash
# Exportar métricas para análisis
curl http://localhost:8000/metrics > metrics_$(date +%Y%m).txt
```

---

## 🚨 **TROUBLESHOOTING**

### **Problemas Comunes**

#### **1. Base de Datos No Conecta**
```bash
# Verificar servicio PostgreSQL
sudo systemctl status postgresql

# Verificar conexión
psql -h localhost -U nexum_user -d nexum_ia

# Verificar variables de entorno
echo $DATABASE_URL
```

#### **2. Rate Limiting Muy Restrictivo**
```bash
# Ajustar límites en .env
API_RATE_LIMIT=200
API_RATE_LIMIT_WINDOW=60
```

#### **3. Logs No Se Generan**
```bash
# Verificar permisos
ls -la logs/

# Verificar configuración
echo $LOG_LEVEL
echo $ENVIRONMENT
```

#### **4. Métricas No Disponibles**
```bash
# Verificar endpoint
curl -v http://localhost:8000/metrics

# Verificar configuración
echo $ENABLE_METRICS
```

### **Comandos de Diagnóstico**

#### **1. Health Check Completo**
```bash
#!/bin/bash
# health_check.sh

echo "=== HEALTH CHECK NEXUM IA ==="

# Verificar API
echo "1. Verificando API..."
curl -f http://localhost:8000/health || echo "❌ API no responde"

# Verificar base de datos
echo "2. Verificando base de datos..."
psql -d nexum_ia -c "SELECT 1;" || echo "❌ DB no conecta"

# Verificar logs
echo "3. Verificando logs..."
tail -1 logs/app.log || echo "❌ No hay logs"

# Verificar métricas
echo "4. Verificando métricas..."
curl -f http://localhost:8000/metrics > /dev/null || echo "❌ Métricas no disponibles"

echo "=== FIN HEALTH CHECK ==="
```

#### **2. Logs de Debug**
```bash
# Habilitar debug temporal
export LOG_LEVEL=DEBUG
export DEBUG=true

# Reiniciar aplicación
sudo systemctl restart nexum_ia
```

---

## 📞 **CONTACTO Y SOPORTE**

### **Información de Contacto**
- **Email**: soporte@tu-dominio.com
- **Slack**: #nexum-ia-support
- **Documentación**: https://docs.tu-dominio.com

### **Escalación de Problemas**
1. **Nivel 1**: Verificar logs y health checks
2. **Nivel 2**: Revisar métricas y performance
3. **Nivel 3**: Contactar equipo de desarrollo

---

## 📋 **CHECKLIST DE PRODUCCIÓN**

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
- [ ] Health check pasa
- [ ] Métricas disponibles
- [ ] Logs se generan
- [ ] Backups funcionan
- [ ] Alertas configuradas
- [ ] Performance aceptable
- [ ] Seguridad verificada

### **Monitoreo Continuo**
- [ ] Logs se revisan diariamente
- [ ] Métricas se monitorean
- [ ] Backups se verifican
- [ ] Alertas funcionan
- [ ] Performance se optimiza
- [ ] Seguridad se audita 