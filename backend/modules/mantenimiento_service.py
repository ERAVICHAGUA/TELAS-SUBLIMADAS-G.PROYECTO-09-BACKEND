# backend/modules/mantenimiento_service.py
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, or_
from .db import SessionLocal
from .models import (
    EventoMantenimiento, 
    OrdenMantenimiento, 
    UmbralAlerta,
    Inspeccion,
    Lote
)
from typing import Optional, Dict, List
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import json


class MantenimientoService:
    """
    Servicio para gestión de mantenimiento preventivo:
    - Detección de patrones y umbrales
    - Creación automática de órdenes de mantenimiento
    - Gestión de eventos y órdenes
    """
    
    @staticmethod
    def registrar_evento(
        maquina: str,
        tipo_evento: str,
        inspeccion_id: Optional[int] = None,
        lote_id: Optional[int] = None,
        turno: Optional[str] = None,
        responsable: Optional[str] = None
    ) -> Dict:
        """
        Registra un evento de mantenimiento y verifica si debe crear una orden preventiva.
        """
        db = SessionLocal()
        try:
            # Crear evento
            nuevo_evento = EventoMantenimiento(
                maquina=maquina,
                tipo_evento=tipo_evento,
                inspeccion_id=inspeccion_id,
                lote_id=lote_id,
                turno=turno,
                responsable=responsable,
                estado="ABIERTA",
                fecha_hora=datetime.now()
            )
            
            db.add(nuevo_evento)
            db.commit()
            db.refresh(nuevo_evento)
            
            # Verificar si debe crear orden preventiva
            orden_info = MantenimientoService._verificar_y_crear_orden(
                db=db,
                maquina=maquina,
                tipo_evento=tipo_evento,
                nuevo_evento_id=nuevo_evento.id
            )
            
            # Si se creó una orden, asociar el evento
            if orden_info.get("orden_creada") and orden_info.get("orden_id"):
                nuevo_evento.orden_mantenimiento_id = orden_info["orden_id"]
                db.commit()
            
            return {
                "evento_id": nuevo_evento.id,
                "orden_info": orden_info
            }
        
        finally:
            db.close()
    
    @staticmethod
    def _verificar_y_crear_orden(
        db: Session,
        maquina: str,
        tipo_evento: str,
        nuevo_evento_id: int
    ) -> Dict:
        """
        Verifica umbrales y crea orden preventiva si es necesario.
        Evita duplicados para el mismo patrón y máquina.
        """
        # Buscar umbral configurado para esta máquina y tipo de defecto
        umbral = db.query(UmbralAlerta).filter(
            and_(
                UmbralAlerta.maquina == maquina,
                UmbralAlerta.tipo_defecto == tipo_evento,
                UmbralAlerta.activo == True
            )
        ).first()
        
        if not umbral:
            # Si no hay umbral configurado, usar valores por defecto
            umbral_eventos = 3
            ventana_tiempo_minutos = 60
            umbral_porcentaje_lote = 5.0
        else:
            umbral_eventos = umbral.umbral_eventos
            ventana_tiempo_minutos = umbral.ventana_tiempo_minutos
            umbral_porcentaje_lote = umbral.umbral_porcentaje_lote
        
        # Verificar si ya existe una orden abierta para este patrón y máquina
        orden_existente = db.query(OrdenMantenimiento).filter(
            and_(
                OrdenMantenimiento.maquina == maquina,
                OrdenMantenimiento.tipo_patron == tipo_evento,
                OrdenMantenimiento.estado.in_(["ABIERTA", "EN_PROGRESO"])
            )
        ).first()
        
        if orden_existente:
            # Si existe, solo agregar el evento a la orden existente
            return {
                "orden_creada": False,
                "orden_existente": True,
                "orden_id": orden_existente.id,
                "mensaje": "Evento agregado a orden existente"
            }
        
        # Calcular ventana de tiempo
        fecha_limite = datetime.now() - timedelta(minutes=ventana_tiempo_minutos)
        
        # Contar eventos similares en la ventana de tiempo
        eventos_recientes = db.query(EventoMantenimiento).filter(
            and_(
                EventoMantenimiento.maquina == maquina,
                EventoMantenimiento.tipo_evento == tipo_evento,
                EventoMantenimiento.fecha_hora >= fecha_limite,
                EventoMantenimiento.orden_mantenimiento_id.is_(None)  # No asociados a orden
            )
        ).count()
        
        # Verificar umbral de eventos
        cumple_umbral_eventos = eventos_recientes >= umbral_eventos
        
        # Verificar umbral de porcentaje del lote (si aplica)
        cumple_umbral_lote = False
        if umbral_porcentaje_lote:
            # Obtener el lote más reciente para esta máquina
            evento_reciente = db.query(EventoMantenimiento).filter(
                and_(
                    EventoMantenimiento.maquina == maquina,
                    EventoMantenimiento.tipo_evento == tipo_evento,
                    EventoMantenimiento.fecha_hora >= fecha_limite
                )
            ).order_by(EventoMantenimiento.fecha_hora.desc()).first()
            
            if evento_reciente and evento_reciente.lote_id:
                lote = db.query(Lote).filter(Lote.id == evento_reciente.lote_id).first()
                if lote:
                    # Contar inspecciones del lote
                    total_inspecciones = db.query(Inspeccion).filter(
                        Inspeccion.lote_id == lote.id
                    ).count()
                    
                    # Contar inspecciones con este tipo de defecto
                    inspecciones_defecto = db.query(Inspeccion).filter(
                        and_(
                            Inspeccion.lote_id == lote.id,
                            Inspeccion.categoria == tipo_evento
                        )
                    ).count()
                    
                    if total_inspecciones > 0:
                        porcentaje = (inspecciones_defecto / total_inspecciones) * 100
                        cumple_umbral_lote = porcentaje >= umbral_porcentaje_lote
        
        # Si cumple algún umbral, crear orden preventiva
        if cumple_umbral_eventos or cumple_umbral_lote:
            # Determinar prioridad
            prioridad = "ALTA" if cumple_umbral_eventos and cumple_umbral_lote else "MEDIA"
            
            # Calcular ventana sugerida (próximas 24 horas)
            ventana_sugerida = datetime.now() + timedelta(hours=24)
            
            nueva_orden = OrdenMantenimiento(
                maquina=maquina,
                tipo_patron=tipo_evento,
                prioridad=prioridad,
                estado="ABIERTA",
                ventana_sugerida=ventana_sugerida,
                fecha_creacion=datetime.now()
            )
            
            db.add(nueva_orden)
            db.commit()
            db.refresh(nueva_orden)
            
            # Asociar todos los eventos recientes a esta orden
            eventos_para_asociar = db.query(EventoMantenimiento).filter(
                and_(
                    EventoMantenimiento.maquina == maquina,
                    EventoMantenimiento.tipo_evento == tipo_evento,
                    EventoMantenimiento.fecha_hora >= fecha_limite,
                    EventoMantenimiento.orden_mantenimiento_id.is_(None)
                )
            ).all()
            
            for evento in eventos_para_asociar:
                evento.orden_mantenimiento_id = nueva_orden.id
            
            db.commit()
            
            return {
                "orden_creada": True,
                "orden_id": nueva_orden.id,
                "prioridad": prioridad,
                "eventos_asociados": len(eventos_para_asociar),
                "mensaje": f"Orden preventiva creada por {len(eventos_para_asociar)} eventos en {ventana_tiempo_minutos} minutos"
            }
        
        return {
            "orden_creada": False,
            "eventos_recientes": eventos_recientes,
            "umbral_requerido": umbral_eventos,
            "mensaje": "Umbral no alcanzado"
        }
    
    @staticmethod
    def obtener_alertas_activas(maquina: Optional[str] = None) -> List[Dict]:
        """
        Obtiene todas las alertas/órdenes activas (ABIERTA o EN_PROGRESO).
        """
        db = SessionLocal()
        try:
            query = db.query(OrdenMantenimiento).filter(
                OrdenMantenimiento.estado.in_(["ABIERTA", "EN_PROGRESO"])
            )
            
            if maquina:
                query = query.filter(OrdenMantenimiento.maquina == maquina)
            
            ordenes = query.order_by(
                OrdenMantenimiento.prioridad.desc(),
                OrdenMantenimiento.fecha_creacion.asc()
            ).all()
            
            resultado = []
            for orden in ordenes:
                # Contar eventos asociados
                eventos_count = db.query(EventoMantenimiento).filter(
                    EventoMantenimiento.orden_mantenimiento_id == orden.id
                ).count()
                
                resultado.append({
                    "id": orden.id,
                    "maquina": orden.maquina,
                    "tipo_patron": orden.tipo_patron,
                    "prioridad": orden.prioridad,
                    "estado": orden.estado,
                    "ventana_sugerida": orden.ventana_sugerida.isoformat() if orden.ventana_sugerida else None,
                    "responsable": orden.responsable,
                    "fecha_creacion": orden.fecha_creacion.isoformat(),
                    "eventos_asociados": eventos_count,
                    "creado_por": orden.creado_por
                })
            
            return resultado
        
        finally:
            db.close()
    
    @staticmethod
    def obtener_historial(
        maquina: Optional[str] = None,
        fecha_inicio: Optional[datetime] = None,
        fecha_fin: Optional[datetime] = None,
        estado: Optional[str] = None,
        tipo_evento: Optional[str] = None
    ) -> List[Dict]:
        """
        Obtiene el historial de eventos y órdenes de mantenimiento.
        """
        db = SessionLocal()
        try:
            query = db.query(EventoMantenimiento)
            
            if maquina:
                query = query.filter(EventoMantenimiento.maquina == maquina)
            
            if fecha_inicio:
                query = query.filter(EventoMantenimiento.fecha_hora >= fecha_inicio)
            
            if fecha_fin:
                fecha_fin_completa = datetime.combine(fecha_fin.date(), datetime.max.time())
                query = query.filter(EventoMantenimiento.fecha_hora <= fecha_fin_completa)
            
            if estado:
                query = query.filter(EventoMantenimiento.estado == estado)
            
            if tipo_evento:
                query = query.filter(EventoMantenimiento.tipo_evento == tipo_evento)
            
            eventos = query.order_by(EventoMantenimiento.fecha_hora.desc()).all()
            
            resultado = []
            for evento in eventos:
                lote = None
                if evento.lote_id:
                    lote = db.query(Lote).filter(Lote.id == evento.lote_id).first()
                
                resultado.append({
                    "id": evento.id,
                    "maquina": evento.maquina,
                    "tipo_evento": evento.tipo_evento,
                    "fecha_hora": evento.fecha_hora.isoformat(),
                    "lote": lote.codigo_lote if lote else None,
                    "turno": evento.turno,
                    "responsable": evento.responsable,
                    "estado": evento.estado,
                    "orden_mantenimiento_id": evento.orden_mantenimiento_id
                })
            
            return resultado
        
        finally:
            db.close()
    
    @staticmethod
    def marcar_orden_realizada(
        orden_id: int,
        accion_correctiva: str,
        evidencia: Optional[str] = None,
        usuario: Optional[str] = None
    ) -> Dict:
        """
        Marca una orden de mantenimiento como realizada.
        """
        db = SessionLocal()
        try:
            orden = db.query(OrdenMantenimiento).filter(
                OrdenMantenimiento.id == orden_id
            ).first()
            
            if not orden:
                return {"success": False, "mensaje": "Orden no encontrada"}
            
            orden.estado = "REALIZADA"
            orden.accion_correctiva = accion_correctiva
            orden.evidencia = evidencia
            orden.fecha_cierre = datetime.now()
            orden.cerrado_por = usuario
            
            # Actualizar estado de eventos asociados
            eventos = db.query(EventoMantenimiento).filter(
                EventoMantenimiento.orden_mantenimiento_id == orden_id
            ).all()
            
            for evento in eventos:
                evento.estado = "REALIZADA"
            
            db.commit()
            
            return {
                "success": True,
                "mensaje": "Orden marcada como realizada",
                "orden_id": orden.id,
                "eventos_actualizados": len(eventos)
            }
        
        finally:
            db.close()
    
    @staticmethod
    def asignar_responsable(orden_id: int, responsable: str, usuario: Optional[str] = None) -> Dict:
        """
        Asigna un responsable a una orden de mantenimiento.
        """
        db = SessionLocal()
        try:
            orden = db.query(OrdenMantenimiento).filter(
                OrdenMantenimiento.id == orden_id
            ).first()
            
            if not orden:
                return {"success": False, "mensaje": "Orden no encontrada"}
            
            orden.responsable = responsable
            if orden.estado == "ABIERTA":
                orden.estado = "EN_PROGRESO"
            
            db.commit()
            
            return {
                "success": True,
                "mensaje": "Responsable asignado",
                "orden_id": orden.id
            }
        
        finally:
            db.close()
    
    @staticmethod
    def configurar_umbral(
        maquina: str,
        tipo_defecto: str,
        umbral_eventos: int = 3,
        ventana_tiempo_minutos: int = 60,
        umbral_porcentaje_lote: Optional[float] = None,
        activo: bool = True
    ) -> Dict:
        """
        Configura o actualiza un umbral de alerta para una máquina y tipo de defecto.
        """
        db = SessionLocal()
        try:
            # Buscar umbral existente
            umbral = db.query(UmbralAlerta).filter(
                and_(
                    UmbralAlerta.maquina == maquina,
                    UmbralAlerta.tipo_defecto == tipo_defecto
                )
            ).first()
            
            if umbral:
                # Actualizar existente
                umbral.umbral_eventos = umbral_eventos
                umbral.ventana_tiempo_minutos = ventana_tiempo_minutos
                umbral.umbral_porcentaje_lote = umbral_porcentaje_lote
                umbral.activo = activo
                accion = "actualizado"
            else:
                # Crear nuevo
                umbral = UmbralAlerta(
                    maquina=maquina,
                    tipo_defecto=tipo_defecto,
                    umbral_eventos=umbral_eventos,
                    ventana_tiempo_minutos=ventana_tiempo_minutos,
                    umbral_porcentaje_lote=umbral_porcentaje_lote,
                    activo=activo
                )
                db.add(umbral)
                accion = "creado"
            
            db.commit()
            db.refresh(umbral)
            
            return {
                "success": True,
                "mensaje": f"Umbral {accion} correctamente",
                "umbral_id": umbral.id
            }
        
        finally:
            db.close()
    
    @staticmethod
    def listar_umbrales(maquina: Optional[str] = None, activo: Optional[bool] = None) -> List[Dict]:
        """
        Lista los umbrales configurados.
        """
        db = SessionLocal()
        try:
            query = db.query(UmbralAlerta)
            
            if maquina:
                query = query.filter(UmbralAlerta.maquina == maquina)
            
            if activo is not None:
                query = query.filter(UmbralAlerta.activo == activo)
            
            umbrales = query.order_by(UmbralAlerta.maquina, UmbralAlerta.tipo_defecto).all()
            
            resultado = []
            for umbral in umbrales:
                resultado.append({
                    "id": umbral.id,
                    "maquina": umbral.maquina,
                    "tipo_defecto": umbral.tipo_defecto,
                    "umbral_eventos": umbral.umbral_eventos,
                    "ventana_tiempo_minutos": umbral.ventana_tiempo_minutos,
                    "umbral_porcentaje_lote": umbral.umbral_porcentaje_lote,
                    "activo": umbral.activo,
                    "fecha_creacion": umbral.fecha_creacion.isoformat() if umbral.fecha_creacion else None
                })
            
            return resultado
        
        finally:
            db.close()

