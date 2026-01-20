import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 1. Intentamos leer la variable de entorno que pusimos en Docker
DATABASE_URL = os.getenv("DATABASE_URL")

# 2. Si no existe (por si ejecutas sin docker), usamos SQLite por defecto
if not DATABASE_URL:
    DATABASE_URL = "sqlite:///./onemore.db"

# 3. Configuración según la base de datos
if DATABASE_URL.startswith("sqlite"):
    # SQLite necesita este argumento especial
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    # PostgreSQL NO necesita check_same_thread
    engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()