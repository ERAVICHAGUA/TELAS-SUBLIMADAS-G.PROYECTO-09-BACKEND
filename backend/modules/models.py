# backend/modules/models.py
from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.sql import func
from .db import Base

class Inspeccion(Base):
    __tablename__ = "inspecciones"

    id = Column(Integer, primary_key=True, index=True)
    resultado = Column(String(20))             # APROBADO / RECHAZADO
    max_distancia = Column(Float)              # Distancia máxima detectada
    puntos_defectuosos = Column(String)        # JSON string

  # ejemplos: "Corte incompleto", "Sobrecalentamiento", "Excluido", etc.
    categoria = Column(String(50), index=True, default="Excluido")

    fecha = Column(DateTime(timezone=True), default=func.now())
