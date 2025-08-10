# En tests, se usa sessionmaker para aislar la base de datos de test. Nunca importar Session de pytest.
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
    # Crear dataset por defecto para FKs
    from sqlalchemy.orm import sessionmaker
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        from models.DebtorDataset import DebtorDataset
        if session.query(DebtorDataset).first() is None:
            session.add(DebtorDataset(name="default", description="test", user_id=None))
            session.commit()
        # Exponer DEFAULT_DATASET_ID
        default_dataset = session.query(DebtorDataset).first()
        if default_dataset:
            monkeypatch.setenv("DEFAULT_DATASET_ID", str(default_dataset.id))
    finally:
        session.close()
    yield
