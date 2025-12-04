# backend/modules/models.py
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, ForeignKey, Boolean, Text, Date
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from datetime import datetime  # ← IMPORT NECESARIO
from .db import Base

# ----------------------------
# MODELO LOTE
# ----------------------------
class Lote(Base):
    __tablename__ = "lotes"

    id = Column(Integer, primary_key=True, index=True)
    codigo_lote = Column(String(30), unique=True, index=True)
    inspector = Column(String(100))
    estado = Column(String(20), default="EN PROCESO")
    fecha = Column(DateTime(timezone=True), server_default=func.now())

    # 1:N (un lote tiene muchas inspecciones)
    inspecciones = relationship("Inspeccion", back_populates="lote")


# ----------------------------
# MODELO INSPECCION
# ----------------------------
class Inspeccion(Base):
    __tablename__ = "inspecciones"

    id = Column(Integer, primary_key=True, index=True)
    resultado = Column(String(20))
    max_distancia = Column(Float)
    puntos_defectuosos = Column(String)

    categoria = Column(String(50), index=True, default="Excluido")

    fecha = Column(DateTime(timezone=True), default=func.now())

    # Relación con Lote (opcional)
    lote_id = Column(Integer, ForeignKey("lotes.id"), nullable=True)
    lote = relationship("Lote", back_populates="inspecciones")


# ----------------------------
# MODELO ALERTA
# ----------------------------
class Alert(Base):
    """
    Modelo para registrar alertas cuando se supera el umbral de defectos.
    """
    __tablename__ = "alertas"

    id = Column(Integer, primary_key=True, index=True)
    tipo_alerta = Column(String(50))
    porcentaje_defectos = Column(Float)
    total_inspecciones = Column(Integer)
    total_rechazados = Column(Integer)
    umbral_configurado = Column(Float)
    recomendacion = Column(Text)
    notificacion_enviada = Column(Boolean, default=False)
    fecha = Column(DateTime(timezone=True), default=func.now())

# ==========================================
# Tabla Reporte Semanal
# ==========================================
class ReporteSemanal(Base):
    __tablename__ = "reportes_semanales"

    id = Column(Integer, primary_key=True, index=True)
    fecha_inicio = Column(Date)
    fecha_fin = Column(Date)
    total_inspecciones = Column(Integer)
    total_rechazados = Column(Integer)
    total_aprobados = Column(Integer)
    porcentaje_defectos = Column(Float)
    tendencia = Column(Float)  # diferencia vs semana anterior
    generado_en = Column(DateTime, default=datetime.utcnow)


