# En tests, se usa sessionmaker para aislar la base de datos de test. Nunca importar Session de pytest.
import base64
import os
import pytest


@pytest.fixture(autouse=True)
def test_env(monkeypatch):
    """Fixture que configura el entorno de test y crea la base de datos."""
    monkeypatch.setenv("SECRET_KEY", "test_secret_key")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///./test.db")
    monkeypatch.setenv("DISABLE_RATE_LIMITER", "true")
    
    # Fernet key debe ser 32 bytes base64 urlsafe
    key = base64.urlsafe_b64encode(b"0" * 32).decode()
    monkeypatch.setenv("ENCRYPTION_KEY", key)
    
    # Limpiar base de datos de pruebas y módulos para evitar conflictos
    import sys
    try:
        db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "test.db")
        if os.path.exists(db_path):
            os.remove(db_path)
    except Exception:
        pass

    # Purgar módulos de models y dependencias para asegurar un estado limpio
    to_delete = [name for name in list(sys.modules.keys()) if name == "db.db" or name == "core.security" or name.startswith("models")]
    for module_name in to_delete:
        try:
            del sys.modules[module_name]
        except KeyError:
            pass
    
    # Importar db y modelos para registrar metadata
    from db.db import Base, engine
    # Importar explícitamente todos los modelos para registrar relaciones antes de create_all
    import models  # noqa: F401
    from models import User, Debtor, Campaign, Strategy, DebtorDataset, DebtorCustomField, DebtPayment, Bot  # noqa: F401
    
    # Crear todas las tablas
    Base.metadata.create_all(bind=engine)
    
    # Crear datos de prueba básicos
    from sqlalchemy.orm import sessionmaker
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Crear usuario de prueba primero
        test_user = session.query(User).filter(User.email == "test@example.com").first()
        if not test_user:
            test_user = User(
                email="test@example.com",
                hashed_password="test_hashed_password",
                role="admin"
            )
            session.add(test_user)
            session.commit()
            session.refresh(test_user)
        
        # Crear dataset por defecto para FKs
        default_dataset = session.query(DebtorDataset).filter(DebtorDataset.name == "default").first()
        if not default_dataset:
            default_dataset = DebtorDataset(
                name="default", 
                user_id=test_user.id
            )
            session.add(default_dataset)
            session.commit()
            session.refresh(default_dataset)
        
        # Exponer DEFAULT_DATASET_ID
        monkeypatch.setenv("DEFAULT_DATASET_ID", str(default_dataset.id))
        
    except Exception as e:
        print(f"Error en test_env: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        session.close()
    
    yield
