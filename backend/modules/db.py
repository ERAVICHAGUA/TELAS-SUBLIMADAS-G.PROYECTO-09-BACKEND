# backend/modules/db.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv
import os

# Obtener la ruta del directorio backend (donde está el .env)
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ENV_PATH = os.path.join(BASE_DIR, ".env")

# Cargar variables de entorno desde el archivo .env en la carpeta backend
load_dotenv(dotenv_path=ENV_PATH)

# ---------------------------------------------------------
# CONFIGURACIÓN DE LA BASE DE DATOS (MySQL local)
# ---------------------------------------------------------

# Configuración de MySQL desde variables de entorno (TODO desde .env)
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "telas_sublimadas")

# Construir URL de conexión MySQL
# Formato: mysql+pymysql://usuario:contraseña@host:puerto/nombre_bd
DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Crear engine con configuración para MySQL
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # Verifica conexiones antes de usarlas
    pool_recycle=3600,   # Recicla conexiones cada hora
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

