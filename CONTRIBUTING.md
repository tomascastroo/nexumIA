# Contribuir a NexumIA

Gracias por tu interés. Antes de enviar cambios:

1. Fork + branch: `feat/`, `fix/`, `chore/`
2. Estilo de commits: Conventional Commits
3. Ejecuta `./verify.sh` localmente (tests + linters + secretos)
4. Añade tests para nuevas funcionalidades
5. Abre PR con descripción, screenshots y checklist

## Estándares
- Python: black, isort, flake8, mypy
- Frontend: ESLint + Prettier
- Tests: pytest / RTL + Jest

## Entorno
- Backend: Python 3.10+, Redis, Celery
- Frontend: Node 18+

## Flujo de PR
- Completa plantilla de PR
- Describe impacto en API si aplica
- Asegura compatibilidad con CI