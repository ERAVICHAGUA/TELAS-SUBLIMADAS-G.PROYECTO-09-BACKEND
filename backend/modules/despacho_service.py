# backend/modules/despacho_service.py

from datetime import datetime
from typing import Dict, Any

from sqlalchemy.orm import Session
from sqlalchemy import func, case

from .models import Lote, Inspeccion, ValidacionLote


def calcular_resumen_lote(db: Session, lote_id: int) -> Dict[str, Any]:
    """
    Devuelve conteo de productos por estado dentro de un lote.
    Estados esperados: APROBADO / RECHAZADO / PENDIENTE (o lo que uses).
    """

    # Aseguramos que el lote exista
    lote = db.query(Lote).filter(Lote.id == lote_id).first()
    if not lote:
        return {
            "existe": False,
            "mensaje": "Lote no encontrado"
        }

    # Agrupar inspecciones por resultado
    rows = (
        db.query(
            Inspeccion.resultado.label("estado"),
            func.count(Inspeccion.id).label("cantidad")
        )
        .filter(Inspeccion.lote_id == lote_id)
        .group_by(Inspeccion.resultado)
        .all()
    )

    total_aprobados = 0
    total_rechazados = 0
    total_pendientes = 0

    for r in rows:
        estado = (r.estado or "").upper()
        if estado == "APROBADO":
            total_aprobados = r.cantidad
        elif estado == "RECHAZADO":
            total_rechazados = r.cantidad
        else:
            # cualquier otro estado lo consideramos PENDIENTE
            total_pendientes += r.cantidad

    total_productos = total_aprobados + total_rechazados + total_pendientes

    puede_despachar = (total_productos > 0) and (total_rechazados == 0) and (total_pendientes == 0)

    return {
        "existe": True,
        "lote_id": lote_id,
        "codigo_lote": lote.codigo_lote,
        "total_productos": total_productos,
        "aprobados": total_aprobados,
        "rechazados": total_rechazados,
        "pendientes": total_pendientes,
        "puede_despachar": puede_despachar,
        "estado_lote": lote.estado,
    }


def registrar_validacion_lote(
    db: Session,
    lote_id: int,
    usuario: str,
    accion: str,
    motivo: str | None = None,
) -> Dict[str, Any]:
    """
    Registra en bitácora una validación (liberar/bloquear) y devuelve el resumen.
    """

    resumen = calcular_resumen_lote(db, lote_id)
    if not resumen.get("existe"):
        return resumen

    validacion = ValidacionLote(
        lote_id=lote_id,
        usuario=usuario,
        accion=accion,
        motivo=motivo,
        fecha_hora=datetime.utcnow(),
        total_aprobados=resumen["aprobados"],
        total_rechazados=resumen["rechazados"],
        total_pendientes=resumen["pendientes"],
    )

    db.add(validacion)

    # Actualizar estado del lote según la acción y la regla
    lote = db.query(Lote).filter(Lote.id == lote_id).first()

    if accion.upper() == "LIBERAR":
        if not resumen["puede_despachar"]:
            # No cumple la regla de 100% aprobado
            return {
                "existe": True,
                "puede_despachar": False,
                "mensaje": "No se puede liberar el lote: existen productos Rechazados o Pendientes.",
                "resumen": resumen,
            }
        lote.estado = "LISTO_PARA_DESPACHO"
    elif accion.upper() == "BLOQUEAR":
        lote.estado = "BLOQUEADO"

    db.commit()
    db.refresh(lote)

    resumen_actualizado = calcular_resumen_lote(db, lote_id)
    return {
        "existe": True,
        "puede_despachar": resumen_actualizado["puede_despachar"],
        "mensaje": f"Validación registrada: {accion}",
        "resumen": resumen_actualizado,
    }


def generar_datos_comprobante(db: Session, lote_id: int) -> Dict[str, Any]:
    """
    Devuelve los datos necesarios para armar el comprobante de validación.
    (El CSV o PDF lo arma el endpoint).
    """
    lote = db.query(Lote).filter(Lote.id == lote_id).first()
    if not lote:
        return {"existe": False, "mensaje": "Lote no encontrado"}

    resumen = calcular_resumen_lote(db, lote_id)

    # Última validación registrada
    ultima_validacion = (
        db.query(ValidacionLote)
        .filter(ValidacionLote.lote_id == lote_id)
        .order_by(ValidacionLote.fecha_hora.desc())
        .first()
    )

    return {
        "existe": True,
        "lote": lote,
        "resumen": resumen,
        "ultima_validacion": ultima_validacion,
    }
