# backend/modules/despacho_router.py

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from io import StringIO
import csv

from .db import get_db
from .despacho_service import (
    calcular_resumen_lote,
    registrar_validacion_lote,
    generar_datos_comprobante,
)

router = APIRouter(
    prefix="/api/despacho",
    tags=["Validación y despacho"]
)


class ValidacionRequest(BaseModel):
    usuario: str
    accion: str  # "LIBERAR" o "BLOQUEAR"
    motivo: str | None = None


@router.get("/lotes/{lote_id}/resumen")
def obtener_resumen_lote(lote_id: int, db: Session = Depends(get_db)):
    """
    Devuelve conteo de aprobados, rechazados y pendientes de un lote,
    y si es despachable o no.
    """
    data = calcular_resumen_lote(db, lote_id)
    if not data.get("existe"):
        raise HTTPException(status_code=404, detail=data["mensaje"])
    return data


@router.post("/lotes/{lote_id}/validar")
def validar_lote(
    lote_id: int,
    body: ValidacionRequest,
    db: Session = Depends(get_db)
):
    """
    Registra una validación (liberar/bloquear) y aplica la regla:
    - Solo se puede LIBERAR si todos los productos están APROBADOS.
    """
    resultado = registrar_validacion_lote(
        db=db,
        lote_id=lote_id,
        usuario=body.usuario,
        accion=body.accion,
        motivo=body.motivo,
    )

    if not resultado.get("existe"):
        raise HTTPException(status_code=404, detail="Lote no encontrado")

    # Si intentó liberar pero no se cumple la regla, devolvemos 400
    if body.accion.upper() == "LIBERAR" and not resultado["puede_despachar"]:
        raise HTTPException(status_code=400, detail=resultado["mensaje"])

    return resultado


@router.get("/lotes/{lote_id}/comprobante")
def generar_comprobante(lote_id: int, db: Session = Depends(get_db)):
    """
    Genera un comprobante de validación en CSV.
    (El frontend puede descargarlo y mostrarlo / imprimirlo).
    """
    data = generar_datos_comprobante(db, lote_id)
    if not data.get("existe"):
        raise HTTPException(status_code=404, detail=data["mensaje"])

    lote = data["lote"]
    resumen = data["resumen"]
    valid = data["ultima_validacion"]

    output = StringIO()
    writer = csv.writer(output)

    writer.writerow(["Comprobante de validación de lote"])
    writer.writerow(["Código de lote", lote.codigo_lote])
    writer.writerow(["Fecha lote", lote.fecha.isoformat()])
    writer.writerow([])

    writer.writerow(["Aprobados", "Rechazados", "Pendientes", "Total"])
    writer.writerow([
        resumen["aprobados"],
        resumen["rechazados"],
        resumen["pendientes"],
        resumen["total_productos"],
    ])

    writer.writerow([])

    if valid:
        writer.writerow(["Última validación"])
        writer.writerow(["Usuario", valid.usuario])
        writer.writerow(["Acción", valid.accion])
        writer.writerow(["Fecha y hora", valid.fecha_hora.isoformat()])
        writer.writerow(["Motivo", valid.motivo or ""])
    else:
        writer.writerow(["Sin validaciones registradas para este lote."])

    output.seek(0)
    filename = f"comprobante_lote_{lote.codigo_lote}.csv"

    return StreamingResponse(
        output,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
