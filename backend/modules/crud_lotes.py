from sqlalchemy.orm import Session
from .db import SessionLocal
from .models import Lote, Inspeccion
from datetime import datetime


def crear_sesion():
    """Crea una sesión temporal para cada operación"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------------------------------------------------
# Crear un nuevo lote
# ---------------------------------------------------------
def crear_lote(
    codigo_lote: str, 
    inspector: str,
    cliente: str = None,
    tipo_producto: str = None,
    orden: str = None
):
    db = SessionLocal()
    try:
        nuevo = Lote(
            codigo_lote=codigo_lote,
            inspector=inspector,
            estado="EN PROCESO",
            fecha=datetime.now(),
            cliente=cliente,
            tipo_producto=tipo_producto,
            orden=orden
        )

        db.add(nuevo)
        db.commit()
        db.refresh(nuevo)
        return nuevo

    finally:
        db.close()


# ---------------------------------------------------------
# Listar todos los lotes
# ---------------------------------------------------------
def listar_lotes():
    db = SessionLocal()
    try:
        return db.query(Lote).order_by(Lote.fecha.desc()).all()
    finally:
        db.close()


# ---------------------------------------------------------
# Obtener lote por ID
# ---------------------------------------------------------
def obtener_lote(id_lote: int):
    db = SessionLocal()
    try:
        return db.query(Lote).filter(Lote.id == id_lote).first()
    finally:
        db.close()


# ---------------------------------------------------------
# Agregar inspección a un lote
# ---------------------------------------------------------
def agregar_inspeccion_a_lote(id_lote: int, id_inspeccion: int):
    db = SessionLocal()
    try:
        lote = db.query(Lote).filter(Lote.id == id_lote).first()
        inspeccion = db.query(Inspeccion).filter(Inspeccion.id == id_inspeccion).first()

        if not lote or not inspeccion:
            return None

        inspeccion.lote_id = id_lote
        db.commit()
        db.refresh(inspeccion)
        return inspeccion

    finally:
        db.close()
