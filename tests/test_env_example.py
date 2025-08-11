import os
import pytest

REQUIRED_VARS = [
    'SECRET_KEY',
    'JWT_ALG',
    'ACCESS_TOKEN_EXPIRE_MINUTES',
    'API_RATE_LIMIT',
    'API_RATE_LIMIT_WINDOW',
    'ALLOWED_ORIGINS',
    'REDIS_URL',
    'REDIS_HOST',
    'REDIS_PORT',
    'REDIS_DB',
    'LOG_LEVEL',
    'APP_ENV',
]

def test_env_example_exists():
    assert os.path.exists('.env.example'), ".env.example file must exist in project root."

def test_env_example_has_required_vars():
    with open('.env.example') as f:
        content = f.read()
    for var in REQUIRED_VARS:
        assert var in content, f"{var} missing in .env.example"