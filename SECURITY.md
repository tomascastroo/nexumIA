# Seguridad en Nexum IA

## Reporte de vulnerabilidades

Si encuentras una vulnerabilidad, por favor repórtala de inmediato a security@nexumia.com o abre un issue con la etiqueta `security` (sin detalles sensibles públicos).

## Soporte de versiones

- Solo la rama principal y la última versión estable reciben parches de seguridad.
- Las ramas legacy pueden no recibir fixes críticos.

## Prácticas de seguridad

- Rotación periódica de secretos y credenciales.
- Uso de `.env.example` como plantilla segura, nunca subir `.env` reales.
- Uso de pre-commit y CI para lint, SAST y escaneo de secretos.
- Headers de seguridad y CORS estrictos en producción.
- Rate limiting y monitoreo de logs.

## Rotación de secretos

- Cambia tus claves y tokens al menos cada 90 días o ante sospecha de filtración.
- Usa gestores de secretos (ej: AWS Secrets Manager, Vault) en producción.

## Escaneo de secretos

- Se ejecuta Gitleaks en CI para detectar posibles filtraciones.
- Puedes correrlo localmente:

```bash
gitleaks detect --source=. --redact
```

## Contacto

security@nexumia.com