from sqlalchemy.orm import Session
from .db import SessionLocal
from .models import Inspeccion
import json
from datetime import datetime
from .rules_clasificacion import clasificar_defecto


def get_db():
    """Crea una sesión nueva por cada operación CRUD."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def guardar_inspeccion(resultado: str, max_distancia: float, puntos_defectuosos: list):
    """
    Guarda los datos de inspección en SQLite.
    Esta versión NO recibe 'db' porque crea su propia sesión interna.
    """
    db = SessionLocal()

    try:
        nueva = Inspeccion(
            resultado=resultado,
            max_distancia=max_distancia,
            puntos_defectuosos=json.dumps(puntos_defectuosos),
            fecha=datetime.now()
        )

        db.add(nueva)
        db.commit()
        db.refresh(nueva)

        return nueva

    finally:
        db.close()

def guardar_inspeccion_clasificada(
    resultado: str,
    max_distancia: float,
    puntos_defectuosos: list,
    descripcion: str,
    color_borde: str,
    caracteristica_borde: str,
    profundidad_corte: float,
    espesor_material: float,
    dimension_fuera_rango: bool,
    falla_maquina: bool,
    desalineado: bool,
    deformacion_material: bool
):
    """
    NUEVA función para la HU de CLASIFICACIÓN.
    """

    db = SessionLocal()

    try:
        # 1) Armar los datos que necesita el sistema experto
        data = {
            "resultado": resultado,
            "max_distancia": max_distancia,
            "puntos_defectuosos": puntos_defectuosos,
            "descripcion": descripcion,
            "color_borde": color_borde,
            "caracteristica_borde": caracteristica_borde,
            "profundidad_corte": profundidad_corte,
            "espesor_material": espesor_material,
            "dimension_fuera_rango": dimension_fuera_rango,
            "falla_maquina": falla_maquina,
            "desalineado": desalineado,
            "deformacion_material": deformacion_material,
        }

        # 2) Pedirle al sistema experto la categoría
        categoria = clasificar_defecto(data)

        # 3) Guardar la inspección con la categoría incluida
        nueva = Inspeccion(
            resultado=resultado,
            max_distancia=max_distancia,
            puntos_defectuosos=json.dumps(puntos_defectuosos),
            categoria=categoria,           # 👈 AQUÍ usamos la categoría
            fecha=datetime.now()
        )

        db.add(nueva)
        db.commit()
        db.refresh(nueva)

        return nueva

    finally:
        db.close()

def listar_inspecciones():
    db = SessionLocal()
    try:
        return db.query(Inspeccion).order_by(Inspeccion.fecha.desc()).all()
    finally:
        db.close()

def obtener_estadisticas_por_categoria():
    """
    Retorna la cantidad de inspecciones agrupadas por categoría.
    Esto se usa para el gráfico del frontend.
    """
    db = SessionLocal()
    try:
        from sqlalchemy import func

        resultados = (
            db.query(Inspeccion.categoria, func.count(Inspeccion.id))
            .group_by(Inspeccion.categoria)
            .all()
        )

        # Convertimos la respuesta en un diccionario
        estadisticas = {categoria: cantidad for categoria, cantidad in resultados}

        return estadisticas

    finally:
        db.close()


def filtrar_por_categoria(categoria: str):
    """
    Devuelve todas las inspecciones que pertenecen a una categoría específica.
    """
    db = SessionLocal()
    try:
        return (
            db.query(Inspeccion)
            .filter(Inspeccion.categoria == categoria)
            .order_by(Inspeccion.fecha.desc())
            .all()
        )
    finally:
        db.close()

def eliminar_inspeccion(id: int):
    """
    Elimina una inspección por ID.
    """
    db = SessionLocal()
    try:
        objeto = db.query(Inspeccion).filter(Inspeccion.id == id).first()

        if not objeto:
            return None  # No existe

        db.delete(objeto)
        db.commit()

        return True  # Eliminado correctamente

    finally:
        db.close()
