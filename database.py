from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Esto creará un archivo 'onemore.db' en la carpeta backend
SQLALCHEMY_DATABASE_URL = "sqlite:///./onemore.db"

# connect_args={"check_same_thread": False} es necesario solo para SQLite
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
