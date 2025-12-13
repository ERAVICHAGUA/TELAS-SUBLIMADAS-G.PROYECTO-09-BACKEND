# backend/modules/db.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

# ---------------------------------------------------------
# CONFIGURACIÓN DE LA BASE DE DATOS (SQLite local)
# ---------------------------------------------------------

# Carpeta backend/
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# Ruta completa a database.db dentro de backend/
#DATABASE_PATH = os.path.join(BASE_DIR, "database.db")

# Formato correcto para SQLite
DATABASE_URL = (
    "postgresql+psycopg2://postgres:TSG-Proyecto09-2025!@"
    "3.19.91.139:5432/telas_sublimadas_db"
)


# Crear engine
engine = create_engine(
    DATABASE_URL,
    #connect_args={"check_same_thread": False},  # Necesario para SQLite
    echo=False  # Cambia a True si quieres ver las queries en consola
)

# Sesión de base de datos
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para los modelos
Base = declarative_base()


# ---------------------------------------------------------
# FUNCIÓN get_db() PARA FASTAPI
# ---------------------------------------------------------

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

