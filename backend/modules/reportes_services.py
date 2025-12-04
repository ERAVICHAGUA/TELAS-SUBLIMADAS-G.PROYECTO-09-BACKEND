# backend/modules/reportes_service.py

from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import func, case

from . import models


def obtener_reporte_calidad(
    db: Session,
    fecha_inicio: datetime,
    fecha_fin: datetime,
    linea_id: Optional[int] = None,
    producto_id: Optional[int] = None,
) -> Dict[str, Any]:

    Inspeccion = models.Inspeccion  # TU MODELO REAL — YA EXISTE

    # -------------------------------------------------------
    # 1️⃣ FILTRO BASE (por rango de fechas)
    # -------------------------------------------------------
    query = db.query(Inspeccion).filter(
        Inspeccion.fecha >= fecha_inicio,
        Inspeccion.fecha <= fecha_fin
    )

    # -------------------------------------------------------
    # 2️⃣ FILTROS OPCIONALES
    # -------------------------------------------------------
    if linea_id is not None:
        if hasattr(Inspeccion, "linea_id"):
            query = query.filter(Inspeccion.linea_id == linea_id)

    if producto_id is not None:
        if hasattr(Inspeccion, "producto_id"):
            query = query.filter(Inspeccion.producto_id == producto_id)

    # -------------------------------------------------------
    # 3️⃣ Totales básicos
    # -------------------------------------------------------
    total_piezas = query.count()
    total_defectos = query.filter(Inspeccion.resultado != "APROBADO").count()

    porcentaje_defectos = (
        (total_defectos / total_piezas) * 100 if total_piezas > 0 else 0
    )

    # -------------------------------------------------------
    # 4️⃣ Clasificación por categoría (usa tu campo r.categoria)
    # -------------------------------------------------------
    Categoria = models.Inspeccion  # la categoría está en la inspección

    categorias_data = (
        db.query(
            Inspeccion.categoria.label("categoria"),
            func.count(Inspeccion.id).label("cantidad")
        )
        .filter(
            Inspeccion.fecha >= fecha_inicio,
            Inspeccion.fecha <= fecha_fin,
            Inspeccion.categoria != None
        )
        .group_by(Inspeccion.categoria)
        .all()
    )

    clasificacion_defectos = [
        {"categoria": c.categoria, "cantidad": c.cantidad}
        for c in categorias_data
    ]

    # -------------------------------------------------------
    # 5️⃣ Tendencia diaria
    # -------------------------------------------------------
    tendencia_data = (
        db.query(
            func.date(Inspeccion.fecha).label("dia"),
            func.count(Inspeccion.id).label("piezas"),
            func.sum(
                case((Inspeccion.resultado != "APROBADO", 1), else_=0)
            ).label("defectos")
        )
        .filter(
            Inspeccion.fecha >= fecha_inicio,
            Inspeccion.fecha <= fecha_fin
        )
        .group_by(func.date(Inspeccion.fecha))
        .order_by(func.date(Inspeccion.fecha))
        .all()
    )

    tendencia = [
        {
            "dia": str(t.dia),
            "piezas": t.piezas,
            "defectos": t.defectos,
            "porcentaje_defectos": (t.defectos / t.piezas * 100) if t.piezas > 0 else 0
        }
        for t in tendencia_data
    ]

    return {
        "total_piezas": total_piezas,
        "total_defectos": total_defectos,
        "porcentaje_defectos": porcentaje_defectos,
        "clasificacion_defectos": clasificacion_defectos,
        "tendencia": tendencia,
    }
