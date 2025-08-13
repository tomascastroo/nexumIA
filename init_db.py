from db.db import Base, engine
print("Creando tablas en PostgreSQL...")
Base.metadata.create_all(bind=engine)
