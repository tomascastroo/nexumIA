## Descripción

Breve descripción del cambio y su propósito.

## Tipo de cambio
- [ ] feat: Nueva funcionalidad
- [ ] fix: Bug fix
- [ ] refactor: Refactor sin cambio funcional
- [ ] chore: Infraestructura/DevX
- [ ] ci: Cambios de CI
- [ ] docs: Documentación
- [ ] test: Tests

## Checklist
- [ ] Cambios atómicos (1 tópico = 1 commit) con Conventional Commits
- [ ] Sin secretos en el código (usar variables de entorno y `.env.example`)
- [ ] Rutas protegidas (JWT + roles donde aplique)
- [ ] Backpressure: llamadas a proveedores en background (Celery/BackgroundTasks)
- [ ] Logs estructurados y métricas añadidas donde corresponda
- [ ] Tests actualizados/pasando (auth, servicios, colas)
- [ ] CI en verde (lint, type-check, tests)

## Cómo probar
Instrucciones para reproducir y validar.

## Riesgos / Impacto
Notas de compatibilidad y migraciones si aplica.

