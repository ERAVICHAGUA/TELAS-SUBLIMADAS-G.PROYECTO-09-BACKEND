# backend/modules/crud_historial.py
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from .db import SessionLocal
from .models import Inspeccion, Lote, Auditoria
from datetime import datetime
from typing import Optional, List, Dict
import json


def consultar_historial_calidad(
    cliente: Optional[str] = None,
    fecha_inicio: Optional[datetime] = None,
    fecha_fin: Optional[datetime] = None,
    tipo_producto: Optional[str] = None,
    estado: Optional[str] = None,
    pagina: int = 1,
    por_pagina: int = 20,
    orden: str = "desc"  # 'desc' o 'asc'
) -> Dict:
    """
    Consulta el historial de calidad con filtros y paginación.
    Retorna un diccionario con los registros y metadatos de paginación.
    """
    db = SessionLocal()
    try:
        # Construir query base con JOIN a Lote
        query = db.query(Inspeccion).join(Lote, Inspeccion.lote_id == Lote.id, isouter=True)
        
        # Aplicar filtros
        filtros = []
        
        if cliente:
            filtros.append(Lote.cliente.ilike(f"%{cliente}%"))
        
        if fecha_inicio:
            filtros.append(Inspeccion.fecha >= fecha_inicio)
        
        if fecha_fin:
            # Agregar un día completo para incluir todo el día final
            fecha_fin_completa = datetime.combine(fecha_fin.date(), datetime.max.time())
            filtros.append(Inspeccion.fecha <= fecha_fin_completa)
        
        if tipo_producto:
            filtros.append(Lote.tipo_producto.ilike(f"%{tipo_producto}%"))
        
        if estado:
            # El estado puede estar en Lote o en Inspeccion.resultado
            filtros.append(
                or_(
                    Lote.estado.ilike(f"%{estado}%"),
                    Inspeccion.resultado.ilike(f"%{estado}%")
                )
            )
        
        # Aplicar todos los filtros
        if filtros:
            query = query.filter(and_(*filtros))
        
        # Contar total de registros (antes de paginar)
        total_registros = query.count()
        
        # Ordenamiento
        if orden == "asc":
            query = query.order_by(Inspeccion.fecha.asc())
        else:
            query = query.order_by(Inspeccion.fecha.desc())
        
        # Paginación
        offset = (pagina - 1) * por_pagina
        registros = query.offset(offset).limit(por_pagina).all()
        
        # Formatear respuesta
        resultados = []
        for inspeccion in registros:
            lote = inspeccion.lote
            resultados.append({
                "id": inspeccion.id,
                "estado": inspeccion.resultado,
                "fecha_inspeccion": inspeccion.fecha.isoformat() if inspeccion.fecha else None,
                "responsable": lote.inspector if lote else None,
                "lote": lote.codigo_lote if lote else None,
                "orden": lote.orden if lote else None,
                "cliente": lote.cliente if lote else None,
                "tipo_producto": lote.tipo_producto if lote else None,
                "categoria": inspeccion.categoria,
                "max_distancia": inspeccion.max_distancia,
                "observaciones": inspeccion.observaciones or "",
                "puntos_defectuosos": json.loads(inspeccion.puntos_defectuosos) if inspeccion.puntos_defectuosos else []
            })
        
        # Calcular metadatos de paginación
        total_paginas = (total_registros + por_pagina - 1) // por_pagina if total_registros > 0 else 0
        
        return {
            "registros": resultados,
            "paginacion": {
                "pagina_actual": pagina,
                "por_pagina": por_pagina,
                "total_registros": total_registros,
                "total_paginas": total_paginas,
                "tiene_siguiente": pagina < total_paginas,
                "tiene_anterior": pagina > 1
            }
        }
    
    finally:
        db.close()


def registrar_auditoria(
    tipo_accion: str,  # 'CONSULTA' o 'DESCARGA'
    usuario: str,
    cliente: Optional[str] = None,
    fecha_inicio: Optional[datetime] = None,
    fecha_fin: Optional[datetime] = None,
    tipo_producto: Optional[str] = None,
    estado: Optional[str] = None,
    formato_exportacion: Optional[str] = None,  # 'PDF' o 'EXCEL'
    parametros_adicionales: Optional[Dict] = None
):
    """
    Registra una acción de auditoría (consulta o descarga).
    """
    db = SessionLocal()
    try:
        # Construir diccionario de parámetros
        parametros = {
            "cliente": cliente,
            "fecha_inicio": fecha_inicio.isoformat() if fecha_inicio else None,
            "fecha_fin": fecha_fin.isoformat() if fecha_fin else None,
            "tipo_producto": tipo_producto,
            "estado": estado,
            "formato_exportacion": formato_exportacion
        }
        
        if parametros_adicionales:
            parametros.update(parametros_adicionales)
        
        nueva_auditoria = Auditoria(
            tipo_accion=tipo_accion,
            usuario=usuario,
            cliente=cliente,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            tipo_producto=tipo_producto,
            estado=estado,
            formato_exportacion=formato_exportacion,
            parametros_busqueda=json.dumps(parametros, default=str)
        )
        
        db.add(nueva_auditoria)
        db.commit()
        db.refresh(nueva_auditoria)
        
        return nueva_auditoria
    
    finally:
        db.close()


def obtener_historial_completo_para_exportacion(
    cliente: Optional[str] = None,
    fecha_inicio: Optional[datetime] = None,
    fecha_fin: Optional[datetime] = None,
    tipo_producto: Optional[str] = None,
    estado: Optional[str] = None
) -> List[Dict]:
    """
    Obtiene todos los registros (sin paginación) para exportación.
    """
    db = SessionLocal()
    try:
        query = db.query(Inspeccion).join(Lote, Inspeccion.lote_id == Lote.id, isouter=True)
        
        filtros = []
        
        if cliente:
            filtros.append(Lote.cliente.ilike(f"%{cliente}%"))
        
        if fecha_inicio:
            filtros.append(Inspeccion.fecha >= fecha_inicio)
        
        if fecha_fin:
            fecha_fin_completa = datetime.combine(fecha_fin.date(), datetime.max.time())
            filtros.append(Inspeccion.fecha <= fecha_fin_completa)
        
        if tipo_producto:
            filtros.append(Lote.tipo_producto.ilike(f"%{tipo_producto}%"))
        
        if estado:
            filtros.append(
                or_(
                    Lote.estado.ilike(f"%{estado}%"),
                    Inspeccion.resultado.ilike(f"%{estado}%")
                )
            )
        
        if filtros:
            query = query.filter(and_(*filtros))
        
        # Ordenar del más reciente al más antiguo
        registros = query.order_by(Inspeccion.fecha.desc()).all()
        
        resultados = []
        for inspeccion in registros:
            lote = inspeccion.lote
            resultados.append({
                "id": inspeccion.id,
                "estado": inspeccion.resultado,
                "fecha_inspeccion": inspeccion.fecha.isoformat() if inspeccion.fecha else None,
                "responsable": lote.inspector if lote else None,
                "lote": lote.codigo_lote if lote else None,
                "orden": lote.orden if lote else None,
                "cliente": lote.cliente if lote else None,
                "tipo_producto": lote.tipo_producto if lote else None,
                "categoria": inspeccion.categoria,
                "max_distancia": inspeccion.max_distancia,
                "observaciones": inspeccion.observaciones or "",
                "puntos_defectuosos": json.loads(inspeccion.puntos_defectuosos) if inspeccion.puntos_defectuosos else []
            })
        
        return resultados
    
    finally:
        db.close()

