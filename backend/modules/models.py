# backend/modules/models.py
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, Text, Date, text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from datetime import datetime  
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
    fecha = Column(DateTime, server_default=text('CURRENT_TIMESTAMP'))  # Compatible con MySQL
    # Nuevos campos para HU de historial por cliente
    cliente = Column(String(100), index=True, nullable=True)  # Nombre del cliente
    tipo_producto = Column(String(50), index=True, nullable=True)  # Tipo de producto
    orden = Column(String(50), nullable=True)  # Número de orden

    # 1:N (un lote tiene muchas inspecciones)
    inspecciones = relationship("Inspeccion", back_populates="lote")
    cliente_id = Column(Integer, ForeignKey("clientes.id"), nullable=True)
    cliente = relationship("Cliente", back_populates="lotes")

# 👇 NUEVO: historial de validaciones de despacho
    validaciones = relationship(
        "ValidacionLote",
        back_populates="lote",
        cascade="all, delete-orphan"
    )

class ValidacionLote(Base):
    __tablename__ = "validaciones_lote"

    id = Column(Integer, primary_key=True, index=True)
    lote_id = Column(Integer, ForeignKey("lotes.id"), nullable=False)

    usuario = Column(String(100), nullable=False)     # quién validó
    accion  = Column(String(20), nullable=False)      # "LIBERAR" / "BLOQUEAR"
    motivo  = Column(Text, nullable=True)             # opcional

    fecha_hora = Column(DateTime(timezone=True), default=func.now())

    total_aprobados  = Column(Integer, default=0)
    total_rechazados = Column(Integer, default=0)
    total_pendientes = Column(Integer, default=0)

    lote = relationship("Lote", back_populates="validaciones")


# AGREGANDO MODELO CLIENTE:
class Cliente(Base):
    __tablename__ = "clientes"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(150), unique=True, index=True)
    contacto = Column(String(150), nullable=True)

    # Relación 1:N con inspecciones
    lotes = relationship("Lote", back_populates="cliente") #SE MODIFICO INSPECCION POR LOTE


# ----------------------------
# MODELO INSPECCION
# ----------------------------
class Inspeccion(Base):
    __tablename__ = "inspecciones"

    id = Column(Integer, primary_key=True, index=True)
    resultado = Column(String(20))
    max_distancia = Column(Float)
    puntos_defectuosos = Column(Text)  # Cambiado a Text para MySQL (almacena JSON)

    categoria = Column(String(50), index=True, default="Excluido")

    fecha = Column(DateTime, server_default=text('CURRENT_TIMESTAMP'))  # Compatible con MySQL
    
    # Nuevo campo para HU de historial por cliente
    observaciones = Column(Text, nullable=True)  # Observaciones resumidas

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
    fecha = Column(DateTime, server_default=text('CURRENT_TIMESTAMP'))  # Compatible con MySQL


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
    generado_en = Column(DateTime, server_default=text('CURRENT_TIMESTAMP'))  # Compatible con MySQL


# ----------------------------
# MODELO AUDITORIA
# ----------------------------
class Auditoria(Base):
    """
    Modelo para registrar auditoría de consultas y descargas de reportes.
    """
    __tablename__ = "auditoria"

    id = Column(Integer, primary_key=True, index=True)
    tipo_accion = Column(String(50), index=True)  # 'CONSULTA' o 'DESCARGA'
    usuario = Column(String(100), index=True)  # Usuario que realizó la acción
    cliente = Column(String(100), nullable=True)  # Cliente consultado (si aplica)
    fecha_inicio = Column(DateTime, nullable=True)  # Fecha inicio del filtro
    fecha_fin = Column(DateTime, nullable=True)  # Fecha fin del filtro
    tipo_producto = Column(String(50), nullable=True)  # Tipo de producto filtrado
    estado = Column(String(20), nullable=True)  # Estado filtrado
    formato_exportacion = Column(String(10), nullable=True)  # 'PDF' o 'EXCEL' (solo para descargas)
    parametros_busqueda = Column(Text, nullable=True)  # JSON con todos los parámetros usados
    fecha = Column(DateTime, server_default=text('CURRENT_TIMESTAMP'))  # Fecha de la acción
