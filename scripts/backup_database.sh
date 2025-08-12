#!/bin/bash

# ============================================================================
# SCRIPT DE BACKUP AUTOMÁTICO DE BASE DE DATOS
# ============================================================================
# Este script debe ejecutarse diariamente via cron
# Agregar a crontab: 0 2 * * * /path/to/scripts/backup_database.sh

# Configuración
DB_NAME="bots_de_cobranza"
DB_USER="postgres"
DB_HOST="localhost"
DB_PORT="5432"
BACKUP_DIR="/var/backups/nexum_ia"
RETENTION_DAYS=30

# Crear directorio de backup si no existe
mkdir -p "$BACKUP_DIR"

# Timestamp para el nombre del archivo
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="$BACKUP_DIR/nexum_ia_backup_$TIMESTAMP.sql"

# Función de logging
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "$BACKUP_DIR/backup.log"
}

# Función de limpieza de backups antiguos
cleanup_old_backups() {
    log "Limpiando backups antiguos (más de $RETENTION_DAYS días)..."
    find "$BACKUP_DIR" -name "nexum_ia_backup_*.sql" -mtime +$RETENTION_DAYS -delete
    find "$BACKUP_DIR" -name "nexum_ia_backup_*.sql.gz" -mtime +$RETENTION_DAYS -delete
}

# Función de verificación de espacio en disco
check_disk_space() {
    local required_space=1024  # 1GB en MB
    local available_space=$(df -m "$BACKUP_DIR" | awk 'NR==2 {print $4}')
    
    if [ "$available_space" -lt "$required_space" ]; then
        log "ERROR: Espacio insuficiente en disco. Disponible: ${available_space}MB, Requerido: ${required_space}MB"
        exit 1
    fi
}

# Función de backup
perform_backup() {
    log "Iniciando backup de la base de datos $DB_NAME..."
    
    # Verificar que pg_dump esté disponible
    if ! command -v pg_dump &> /dev/null; then
        log "ERROR: pg_dump no está instalado"
        exit 1
    fi
    
    # Realizar backup
    if pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
        --verbose --clean --if-exists --no-owner --no-privileges \
        > "$BACKUP_FILE" 2>> "$BACKUP_DIR/backup.log"; then
        
        # Comprimir backup
        gzip "$BACKUP_FILE"
        BACKUP_FILE_COMPRESSED="$BACKUP_FILE.gz"
        
        # Verificar integridad del backup
        if gunzip -t "$BACKUP_FILE_COMPRESSED" 2>/dev/null; then
            log "Backup completado exitosamente: $BACKUP_FILE_COMPRESSED"
            log "Tamaño del backup: $(du -h "$BACKUP_FILE_COMPRESSED" | cut -f1)"
        else
            log "ERROR: Backup corrupto - $BACKUP_FILE_COMPRESSED"
            exit 1
        fi
    else
        log "ERROR: Fallo en el backup de la base de datos"
        exit 1
    fi
}

# Función de backup de solo esquema
perform_schema_backup() {
    log "Realizando backup del esquema..."
    SCHEMA_BACKUP_FILE="$BACKUP_DIR/nexum_ia_schema_$TIMESTAMP.sql"
    
    if pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
        --schema-only --verbose --clean --if-exists --no-owner --no-privileges \
        > "$SCHEMA_BACKUP_FILE" 2>> "$BACKUP_DIR/backup.log"; then
        
        gzip "$SCHEMA_BACKUP_FILE"
        log "Backup de esquema completado: $SCHEMA_BACKUP_FILE.gz"
    else
        log "ERROR: Fallo en el backup del esquema"
    fi
}

# Función de notificación
send_notification() {
    local status=$1
    local message=$2
    
    # Aquí puedes integrar con servicios de notificación como:
    # - Slack webhook
    # - Email
    # - Telegram bot
    # - SMS
    
    log "NOTIFICACIÓN [$status]: $message"
    
    # Ejemplo para Slack (descomentar y configurar):
    # if [ "$status" = "ERROR" ]; then
    #     curl -X POST -H 'Content-type: application/json' \
    #          --data "{\"text\":\"🚨 Backup Error: $message\"}" \
    #          https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK
    # fi
}

# Función principal
main() {
    log "=== INICIO DE BACKUP ==="
    
    # Verificar espacio en disco
    check_disk_space
    
    # Realizar backup completo
    if perform_backup; then
        # Realizar backup de esquema
        perform_schema_backup
        
        # Limpiar backups antiguos
        cleanup_old_backups
        
        # Notificar éxito
        send_notification "SUCCESS" "Backup completado exitosamente"
        log "=== BACKUP COMPLETADO ==="
    else
        # Notificar error
        send_notification "ERROR" "Fallo en el proceso de backup"
        log "=== BACKUP FALLIDO ==="
        exit 1
    fi
}

# Ejecutar función principal
main "$@" 