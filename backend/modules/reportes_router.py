# backend/reportes_router.py

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional

from modules.db import get_db
from modules.reportes_services import obtener_reporte_calidad

router = APIRouter(
    prefix="/api/reportes",
    tags=["Reportes de Calidad"]
)

@router.get("/semanal")
def reporte_semanal(
    fecha_inicio: datetime = Query(..., description="Formato YYYY-MM-DD"),
    fecha_fin: datetime = Query(..., description="Formato YYYY-MM-DD"),
    linea_id: Optional[int] = None,
    producto_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """
    Devuelve el reporte semanal en JSON.
    """
    datos = obtener_reporte_calidad(
        db=db,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        linea_id=linea_id,
        producto_id=producto_id
    )

    return datos
