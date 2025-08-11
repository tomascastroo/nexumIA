# Changelog

Todos los cambios notables a este proyecto se documentarán en este archivo.

## [Unreleased]

## [1.0.0] - 2025-08-10

### feat
- Middleware de rate limiting con Redis e integración en FastAPI
- Tareas Celery para OpenAI y wrappers asíncronos
- Script `verify.sh` para detección de secretos y validación
- Frontend: manejo de expiración JWT y `authFetch`

### fix
- Webhook: asignación de `debtor_dataset_id` por defecto
- Frontend: StrategyTraceability firmado y warning de useEffect
- Deshabilitar Twilio real en tests/CI

### refactor
- Servicios frontend a `authFetch`

### test
- Tests rate limiting y Celery