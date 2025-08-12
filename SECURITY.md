# Política de Seguridad

Si encuentras una vulnerabilidad:

- No abras un issue público.
- Reporta por email a security@nexumia.example con detalles, PoC y alcance.
- Recibirás acuse de recibo en 48h y seguimiento.

## Alcance
- API FastAPI, Celery tasks, middlewares
- Frontend (React)
- Infra (Docker, Redis)

## Prácticas
- Variables de entorno para secretos
- `verify.sh` escanea secretos y ejecuta linters/tests
- Rate limiting activo por defecto (configurable)