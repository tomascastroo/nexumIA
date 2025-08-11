import logging
import os
import sys
import json
from typing import Optional

class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'time': self.formatTime(record, self.datefmt),
        }
        # Agrega request_id y user_id si existen en el record
        if hasattr(record, 'request_id'):
            log_record['request_id'] = record.request_id
        if hasattr(record, 'user_id'):
            log_record['user_id'] = record.user_id
        return json.dumps(log_record)

def get_logger(name: Optional[str] = None):
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JsonFormatter())
        logger.addHandler(handler)
    logger.setLevel(os.getenv('LOG_LEVEL', 'INFO').upper())
    logger.propagate = False
    return logger

# Integración con Uvicorn
class UvicornJsonFormatter(JsonFormatter):
    def format(self, record):
        log_record = super().format(record)
        return log_record

# Para FastAPI/Uvicorn: hook para usar este logger
try:
    import uvicorn
    uvicorn.config.LOGGING_CONFIG["formatters"]["default"]["()"] = UvicornJsonFormatter
except Exception:
    pass