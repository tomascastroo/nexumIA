import hashlib
import hmac
import logging
import json
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import os
from sqlalchemy.orm import Session
from models.User import User

logger = logging.getLogger(__name__)

class UserRole(Enum):
    ADMIN = "admin"
    OPERATOR = "operator"
    MEDICAL = "medical"
    VIEWER = "viewer"

class Permission(Enum):
    # Gestión de deudores
    VIEW_DEBTORS = "view_debtors"
    CREATE_DEBTORS = "create_debtors"
    UPDATE_DEBTORS = "update_debtors"
    DELETE_DEBTORS = "delete_debtors"
    
    # Gestión de campañas
    VIEW_CAMPAIGNS = "view_campaigns"
    CREATE_CAMPAIGNS = "create_campaigns"
    UPDATE_CAMPAIGNS = "update_campaigns"
    DELETE_CAMPAIGNS = "delete_campaigns"
    
    # Gestión de estrategias
    VIEW_STRATEGIES = "view_strategies"
    CREATE_STRATEGIES = "create_strategies"
    UPDATE_STRATEGIES = "update_strategies"
    DELETE_STRATEGIES = "delete_strategies"
    
    # Gestión de pagos
    VIEW_PAYMENTS = "view_payments"
    CREATE_PAYMENTS = "create_payments"
    UPDATE_PAYMENTS = "update_payments"
    
    # Gestión de usuarios
    VIEW_USERS = "view_users"
    CREATE_USERS = "create_users"
    UPDATE_USERS = "update_users"
    DELETE_USERS = "delete_users"
    
    # Analytics y reportes
    VIEW_ANALYTICS = "view_analytics"
    EXPORT_DATA = "export_data"
    
    # Configuración del sistema
    VIEW_CONFIG = "view_config"
    UPDATE_CONFIG = "update_config"

@dataclass
class AuditEvent:
    """Evento de auditoría"""
    timestamp: datetime
    user_id: int
    action: str
    resource_type: str
    resource_id: Optional[int] = None
    details: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

class SecurityService:
    """Servicio de seguridad y control de acceso"""
    
    def __init__(self):
        # Configuración de roles y permisos
        self.role_permissions = {
            UserRole.ADMIN: [
                Permission.VIEW_DEBTORS, Permission.CREATE_DEBTORS, Permission.UPDATE_DEBTORS, Permission.DELETE_DEBTORS,
                Permission.VIEW_CAMPAIGNS, Permission.CREATE_CAMPAIGNS, Permission.UPDATE_CAMPAIGNS, Permission.DELETE_CAMPAIGNS,
                Permission.VIEW_STRATEGIES, Permission.CREATE_STRATEGIES, Permission.UPDATE_STRATEGIES, Permission.DELETE_STRATEGIES,
                Permission.VIEW_PAYMENTS, Permission.CREATE_PAYMENTS, Permission.UPDATE_PAYMENTS,
                Permission.VIEW_USERS, Permission.CREATE_USERS, Permission.UPDATE_USERS, Permission.DELETE_USERS,
                Permission.VIEW_ANALYTICS, Permission.EXPORT_DATA,
                Permission.VIEW_CONFIG, Permission.UPDATE_CONFIG
            ],
            UserRole.OPERATOR: [
                Permission.VIEW_DEBTORS, Permission.CREATE_DEBTORS, Permission.UPDATE_DEBTORS,
                Permission.VIEW_CAMPAIGNS, Permission.CREATE_CAMPAIGNS, Permission.UPDATE_CAMPAIGNS,
                Permission.VIEW_STRATEGIES, Permission.CREATE_STRATEGIES, Permission.UPDATE_STRATEGIES,
                Permission.VIEW_PAYMENTS, Permission.CREATE_PAYMENTS, Permission.UPDATE_PAYMENTS,
                Permission.VIEW_ANALYTICS
            ],
            UserRole.MEDICAL: [
                Permission.VIEW_DEBTORS, Permission.UPDATE_DEBTORS,
                Permission.VIEW_CAMPAIGNS,
                Permission.VIEW_STRATEGIES,
                Permission.VIEW_PAYMENTS,
                Permission.VIEW_ANALYTICS
            ],
            UserRole.VIEWER: [
                Permission.VIEW_DEBTORS,
                Permission.VIEW_CAMPAIGNS,
                Permission.VIEW_STRATEGIES,
                Permission.VIEW_PAYMENTS,
                Permission.VIEW_ANALYTICS
            ]
        }
        
        # Clave de encriptación (en producción, obtener desde variables de entorno)
        env_key = os.getenv('ENCRYPTION_KEY')
        if env_key:
            # Convertir a bytes
            key_candidate = env_key.encode('utf-8')
        else:
            key_candidate = Fernet.generate_key()

        # Validar o hacer fallback si la clave no es válida
        try:
            self.cipher_suite = Fernet(key_candidate)
            self.encryption_key = key_candidate
        except Exception:
            # Fallback seguro para evitar fallas en arranque/tests
            self.encryption_key = Fernet.generate_key()
            self.cipher_suite = Fernet(self.encryption_key)
        
        # Eventos de auditoría en memoria (en producción, usar base de datos)
        self.audit_events: List[AuditEvent] = []
    
    def has_permission(self, user_id: int, permission: Permission, db: Session) -> bool:
        """Verifica si un usuario tiene un permiso específico"""
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return False
            
            user_role = UserRole(user.role) if user.role else UserRole.VIEWER
            return permission in self.role_permissions.get(user_role, [])
            
        except Exception as e:
            logger.error(f"Error verificando permisos: {e}")
            return False
    
    def check_resource_access(self, user_id: int, resource_type: str, resource_id: int, action: str, db: Session) -> bool:
        """Verifica acceso a un recurso específico"""
        try:
            # Verificar permisos básicos
            permission_map = {
                'debtors': Permission.VIEW_DEBTORS,
                'campaigns': Permission.VIEW_CAMPAIGNS,
                'strategies': Permission.VIEW_STRATEGIES,
                'payments': Permission.VIEW_PAYMENTS,
                'users': Permission.VIEW_USERS
            }
            
            base_permission = permission_map.get(resource_type)
            if not base_permission:
                return False
            
            if not self.has_permission(user_id, base_permission, db):
                return False
            
            # Verificar permisos específicos según la acción
            action_permission_map = {
                'create': f"create_{resource_type}",
                'update': f"update_{resource_type}",
                'delete': f"delete_{resource_type}"
            }
            
            if action in action_permission_map:
                action_permission = Permission(action_permission_map[action])
                if not self.has_permission(user_id, action_permission, db):
                    return False
            
            # Log de auditoría
            self.log_audit_event(
                user_id=user_id,
                action=f"{action}_{resource_type}",
                resource_type=resource_type,
                resource_id=resource_id
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error verificando acceso a recurso: {e}")
            return False
    
    def encrypt_sensitive_data(self, data: str) -> str:
        """Encripta datos sensibles"""
        try:
            encrypted_data = self.cipher_suite.encrypt(data.encode())
            return base64.urlsafe_b64encode(encrypted_data).decode()
        except Exception as e:
            logger.error(f"Error encriptando datos: {e}")
            return data
    
    def decrypt_sensitive_data(self, encrypted_data: str) -> str:
        """Desencripta datos sensibles"""
        try:
            decoded_data = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted_data = self.cipher_suite.decrypt(decoded_data)
            return decrypted_data.decode()
        except Exception as e:
            logger.error(f"Error desencriptando datos: {e}")
            return encrypted_data
    
    def hash_password(self, password: str) -> str:
        """Genera hash seguro de contraseña"""
        salt = os.urandom(16)
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        salt_b64 = base64.urlsafe_b64encode(salt).decode()
        return f"{salt_b64}:{key.decode()}"
    
    def verify_password(self, password: str, hashed_password: str) -> bool:
        """Verifica contraseña contra hash"""
        try:
            salt_b64, key_b64 = hashed_password.split(':')
            salt = base64.urlsafe_b64decode(salt_b64.encode())
            key = base64.urlsafe_b64decode(key_b64.encode())
            
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            kdf.verify(password.encode(), key)
            return True
        except Exception as e:
            logger.error(f"Error verificando contraseña: {e}")
            return False
    
    def log_audit_event(
        self,
        user_id: int,
        action: str,
        resource_type: str,
        resource_id: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ):
        """Registra evento de auditoría"""
        try:
            event = AuditEvent(
                timestamp=datetime.utcnow(),
                user_id=user_id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                details=details,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            self.audit_events.append(event)
            
            # En producción, guardar en base de datos
            logger.info(f"AUDIT: User {user_id} performed {action} on {resource_type} {resource_id}")
            
        except Exception as e:
            logger.error(f"Error registrando evento de auditoría: {e}")
    
    def get_audit_events(
        self,
        user_id: Optional[int] = None,
        action: Optional[str] = None,
        resource_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[AuditEvent]:
        """Obtiene eventos de auditoría filtrados"""
        events = self.audit_events
        
        if user_id:
            events = [e for e in events if e.user_id == user_id]
        
        if action:
            events = [e for e in events if action in e.action]
        
        if resource_type:
            events = [e for e in events if e.resource_type == resource_type]
        
        if start_date:
            events = [e for e in events if e.timestamp >= start_date]
        
        if end_date:
            events = [e for e in events if e.timestamp <= end_date]
        
        return sorted(events, key=lambda x: x.timestamp, reverse=True)
    
    def sanitize_user_input(self, text: str) -> str:
        """Sanitiza entrada de usuario para prevenir inyecciones"""
        if not text:
            return ""
        
        # Remover caracteres peligrosos
        dangerous_chars = ['<', '>', '"', "'", '&', '{', '}', '[', ']', '|', '\\', '/']
        sanitized = text
        
        for char in dangerous_chars:
            sanitized = sanitized.replace(char, '')
        
        # Limitar longitud
        if len(sanitized) > 1000:
            sanitized = sanitized[:1000]
        
        return sanitized.strip()
    
    def generate_api_token(self, user_id: int, expires_in_hours: int = 24) -> str:
        """Genera token de API temporal"""
        try:
            exp_ts = int((datetime.utcnow() + timedelta(hours=expires_in_hours)).timestamp())
            payload = {
                'user_id': user_id,
                'exp': exp_ts,
                'type': 'api_token'
            }
            
            # En producción, usar JWT
            token_data = json.dumps(payload)
            return self.encrypt_sensitive_data(token_data)
            
        except Exception as e:
            logger.error(f"Error generando token de API: {e}")
            return ""
    
    def validate_api_token(self, token: str) -> Optional[int]:
        """Valida token de API y retorna user_id"""
        try:
            token_data = self.decrypt_sensitive_data(token)
            payload = json.loads(token_data)
            
            # Verificar expiración
            exp_ts = int(payload['exp'])
            if int(datetime.utcnow().timestamp()) > exp_ts:
                return None
            
            return payload.get('user_id')
            
        except Exception as e:
            logger.error(f"Error validando token de API: {e}")
            return None

# Instancia global del servicio
security_service = SecurityService() 