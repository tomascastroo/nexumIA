# 🚀 GUÍA COMPLETA DE VARIABLES DE ENTORNO

## 📋 Variables YA CONFIGURADAS (No necesitas cambiar)

Estas variables ya están funcionando correctamente:

```bash
# Base de datos
DATABASE_URL=postgresql://postgres:apache@localhost:5432/bots_de_cobranza

# OpenAI API (ya configurada)
OPENAI_API_KEY=
```

## 🔐 Variables CRÍTICAS que NECESITAS configurar

### 1. SECRET_KEY (OBLIGATORIO)
```bash
# Generar una clave secreta segura:
SECRET_KEY=$(openssl rand -hex 32)
# O usar: SECRET_KEY=tu_clave_secreta_de_32_caracteres_minimo
```

### 2. Variables de WhatsApp (si usas WhatsApp)
```bash
WHATSAPP_API_KEY=tu_whatsapp_api_key
WHATSAPP_PHONE_NUMBER_ID=tu_phone_number_id
WHATSAPP_ACCESS_TOKEN=tu_access_token
```

### 3. Variables de Pagos (si usas pagos)
```bash
# MercadoPago
MERCADOPAGO_ACCESS_TOKEN=tu_mercadopago_token
MERCADOPAGO_WEBHOOK_SECRET=tu_mercadopago_webhook_secret

# Stripe
STRIPE_SECRET_KEY=tu_stripe_secret_key
STRIPE_WEBHOOK_SECRET=tu_stripe_webhook_secret
```

## 📝 Cómo configurar tu archivo .env

1. **Copia el archivo de ejemplo:**
```bash
cp env.example .env
```

2. **Edita el archivo .env** y configura las variables críticas:

```bash
# Variables OBLIGATORIAS
SECRET_KEY=tu_secret_key_generado_aqui

# Variables OPCIONALES (solo si usas estos servicios)
WHATSAPP_API_KEY=tu_whatsapp_api_key
MERCADOPAGO_ACCESS_TOKEN=tu_mercadopago_token
STRIPE_SECRET_KEY=tu_stripe_secret_key
```

## 🔍 Variables que YA NO están hardcodeadas

✅ **Arreglado:** OpenAI API key en `services/openai_service.py`
✅ **Arreglado:** Credenciales de base de datos en `alembic.ini`
✅ **Arreglado:** Secret keys de webhooks en `services/webhook_service.py`

## 🚨 Variables que FALTAN obtener

### 1. SECRET_KEY (CRÍTICO)
- **Por qué:** Para JWT tokens y encriptación
- **Cómo obtener:** `openssl rand -hex 32`
- **Ejemplo:** `SECRET_KEY=a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6`

### 2. WhatsApp Business API (OPCIONAL)
- **Por qué:** Para enviar mensajes automáticos
- **Cómo obtener:** 
  1. Crear cuenta en Meta Business
  2. Configurar WhatsApp Business API
  3. Obtener credenciales del panel

### 3. MercadoPago (OPCIONAL)
- **Por qué:** Para procesar pagos
- **Cómo obtener:**
  1. Crear cuenta en MercadoPago Developers
  2. Obtener Access Token
  3. Configurar webhook

### 4. Stripe (OPCIONAL)
- **Por qué:** Para procesar pagos internacionales
- **Cómo obtener:**
  1. Crear cuenta en Stripe
  2. Obtener API keys del dashboard
  3. Configurar webhook

## ✅ Checklist de configuración

- [ ] Generar SECRET_KEY
- [ ] Configurar .env con SECRET_KEY
- [ ] (Opcional) Configurar WhatsApp si lo usas
- [ ] (Opcional) Configurar MercadoPago si lo usas
- [ ] (Opcional) Configurar Stripe si lo usas
- [ ] Probar que la aplicación arranca

## 🧪 Comando para probar configuración

```bash
# Verificar que todas las variables están cargadas
python -c "
import os
from dotenv import load_dotenv
load_dotenv()
print('SECRET_KEY:', '✅' if os.getenv('SECRET_KEY') else '❌')
print('DATABASE_URL:', '✅' if os.getenv('DATABASE_URL') else '❌')
print('OPENAI_API_KEY:', '✅' if os.getenv('OPENAI_API_KEY') else '❌')
"
```

## 🔧 Variables de desarrollo vs producción

### Desarrollo (actual)
```bash
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO
```

### Producción (cuando despliegues)
```bash
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=WARNING
```

---

## 📞 ¿Necesitas ayuda?

Si tienes problemas configurando alguna variable específica, dime cuál y te ayudo a obtenerla paso a paso. 