import base64
import os
import pytest


@pytest.fixture(autouse=True)
def test_env(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "test_secret_key")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///./test.db")
    monkeypatch.setenv("DISABLE_RATE_LIMITER", "true")
    # Fernet key debe ser 32 bytes base64 urlsafe
    key = base64.urlsafe_b64encode(b"0" * 32).decode()
    monkeypatch.setenv("ENCRYPTION_KEY", key)
    # Crear tablas para modelos base
    import sys
    sys.modules.pop("db.db", None)
    from db.db import Base, engine
    # Importar modelos para registrar metadata
    import models.User  # noqa: F401
    import models.Debtor  # noqa: F401
    import models.Campaign  # noqa: F401
    import models.Strategy  # noqa: F401
    import models.DebtorDataset  # noqa: F401
    Base.metadata.create_all(bind=engine)
    yield
