# En tests, se usa sessionmaker para aislar la base de datos de test. Nunca importar Session de pytest.
import base64
import os
import sys
import pytest
# Importar db y modelos para registrar metadata
from db.db import Base, engine
# Importar explícitamente todos los modelos para registrar relaciones antes de create_all
import models  # noqa: F401
from models.User import User
from models.Debtor import Debtor
from models.Campaign import Campaign
from models.Strategy import Strategy
from models.DebtorDataset import DebtorDataset
from models.DebtorCustomField import DebtorCustomField
from models.DebtPayment import DebtPayment
from models.Bot import Bot



# Configuración temprana de entorno para que los módulos de app usen SQLite en tests
os.environ.setdefault("SECRET_KEY", "test_secret_key")
os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")
os.environ.setdefault("DISABLE_RATE_LIMITER", "true")
# Deshabilitar servicios externos (Twilio, etc.) durante pruebas
os.environ.setdefault("DISABLE_EXTERNAL_SERVICES", "true")
# Fernet key de 32 bytes en base64 urlsafe
if not os.getenv("ENCRYPTION_KEY"):
    os.environ["ENCRYPTION_KEY"] = base64.urlsafe_b64encode(b"0" * 32).decode()

# Asegurar que el root del proyecto esté en sys.path para imports como `db.db`
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


@pytest.fixture(autouse=True)
def test_env(monkeypatch):
    """Fixture que configura el entorno de test y crea la base de datos."""
    monkeypatch.setenv("SECRET_KEY", os.getenv("SECRET_KEY", "test_secret_key"))
    monkeypatch.setenv("DATABASE_URL", os.getenv("DATABASE_URL", "sqlite:///./test.db"))
    monkeypatch.setenv("DISABLE_RATE_LIMITER", "true")
    monkeypatch.setenv("DISABLE_EXTERNAL_SERVICES", "true")
    
    # Fernet key debe ser 32 bytes base64 urlsafe
    key = os.getenv("ENCRYPTION_KEY") or base64.urlsafe_b64encode(b"0" * 32).decode()
    monkeypatch.setenv("ENCRYPTION_KEY", key)
    

    
    # Crear todas las tablas (idempotente)
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
                hashed_password="test_hashed_password",  # nosec B106
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

    # Limpieza entre pruebas: vaciar tablas pero mantener schema
    session = Session()
    try:
        # Orden seguro para borrar datos según FKs
        for table in reversed(Base.metadata.sorted_tables):
            session.execute(table.delete())
        session.commit()
    finally:
        session.close()
