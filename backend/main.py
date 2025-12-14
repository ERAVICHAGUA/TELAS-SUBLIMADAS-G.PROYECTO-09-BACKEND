# backend/main.py
import csv
from io import StringIO
from fastapi.responses import StreamingResponse
from modules.crud import eliminar_inspeccion
from fastapi import Path

from apscheduler.schedulers.background import BackgroundScheduler
from modules.reporte_service import ReporteService
scheduler = BackgroundScheduler()

from modules.reportes_router import router as reportes_router
from modules.despacho_router import router as despacho_router

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import json
from modules.db import Base, engine, SessionLocal
from modules.models import ReporteSemanal
from modules.crud import guardar_inspeccion_clasificada
from modules.crud import filtrar_por_categoria
from modules.crud import obtener_estadisticas_por_categoria

from modules import models

# Importamos la lógica de análisis
from modules.analisis import analizar_molde, cargar_contorno_ideal

# Importamos CRUD para guardar y listar registros
from modules.crud import guardar_inspeccion, listar_inspecciones
from modules.crud_lotes import crear_lote, listar_lotes, obtener_lote, agregar_inspeccion_a_lote
from pydantic import BaseModel


class DatosClasificacion(BaseModel):
    descripcion: str
    color_borde: str
    caracteristica_borde: str
    profundidad_corte: float
    espesor_material: float
    dimension_fuera_rango: bool
    falla_maquina: bool
    desalineado: bool
    deformacion_material: bool

class DatosLote(BaseModel):
    codigo_lote: str
    inspector: str
    cliente: Optional[str] = None
    tipo_producto: Optional[str] = None
    orden: Optional[str] = None

class DatosAgregarInspeccion(BaseModel):
    id_inspeccion: int

# NUEVO: Importar servicios de alertas y email
from modules.alert_service import AlertService
from modules.email_service import EmailService

# NUEVO: Importar servicios de historial y exportación
from modules.crud_historial import consultar_historial_calidad, registrar_auditoria, obtener_historial_completo_para_exportacion
from modules.export_service import generar_pdf_historial, generar_excel_historial
from datetime import datetime
from typing import Optional

# ---------------------------------------------------------
# CONFIG FASTAPI
# ---------------------------------------------------------

app = FastAPI(
    title="Sistema de Control de Calidad Láser (Simulación)",
    description="Backend de FastAPI modular para detección de rebaba, registro de inspecciones y sistema de alertas."
)

app.include_router(reportes_router)
app.include_router(despacho_router)

# Configurar CORS (si tienes frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especifica tu dominio
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------
# EVENTO DE INICIO: CARGA DE PLANTILLA IDEAL
# ---------------------------------------------------------

@app.on_event("startup")
def startup_event():
    """Carga la plantilla ideal y crea la base de datos si no existe."""
    
    # Crear tablas de MySQL
    Base.metadata.create_all(bind=engine)
    print("[OK] Base de datos MySQL lista. Tablas creadas.")
    
    # Cargar plantilla ideal
    if not cargar_contorno_ideal():
        print("[WARNING] ADVERTENCIA: No se cargo la plantilla ideal. El analisis no funcionara.")
    
    # NUEVO: Probar conexión SMTP
    print("\n[CONFIG] Probando configuracion de email...")
    EmailService.test_conexion()


    # Iniciar scheduler
    scheduler.add_job(
        ReporteService.generar_reporte_semanal,
        trigger="cron",
        day_of_week="sun",
        hour=23,
        minute=59,
        id="reporte_semanal_auto",
        replace_existing=True
    )

    scheduler.start()
    print("🗓️ Scheduler semanal activado.")

# ---------------------------------------------------------
# ENDPOINT PRINCIPAL: INSPECCIÓN DE MOLDE (CON ALERTAS)
# ---------------------------------------------------------

@app.post("/api/inspeccionar")
async def inspeccionar_calidad(file: UploadFile = File(...)):
    """
    Recibe la imagen y devuelve si está APROBADA o RECHAZADA.
    Además guarda el resultado en MySQL y verifica si debe crear una alerta.
    """
    try:
        # Leer bytes de la imagen
        imagen_bytes = await file.read()

        # Ejecutar análisis
        resultado = analizar_molde(imagen_bytes)

        # Validación de errores
        if resultado.get("status") == "ERROR":
            raise HTTPException(status_code=400, detail=resultado["mensaje"])

        # Guardar resultado en MySQL
        guardar_inspeccion(
            resultado=resultado["status"],
            max_distancia=resultado["max_distancia"],
            puntos_defectuosos=resultado["puntos_defectuosos"],
        )

        # NUEVO: Verificar si se debe crear una alerta automática
        alerta_info = AlertService.verificar_y_crear_alerta()
        
        # Si se creó una alerta, intentar enviar notificación por email
        if alerta_info.get("alerta_creada"):
            stats = alerta_info["estadisticas"]
            email_enviado = EmailService.enviar_alerta_defectos(
                porcentaje=stats["porcentaje_defectos"],
                total_inspecciones=stats["total_inspecciones"],
                total_rechazados=stats["total_rechazados"],
                recomendacion=alerta_info["recomendacion"]
            )
            
            # Marcar alerta como notificada si el email se envió correctamente
            if email_enviado:
                AlertService.marcar_alerta_como_notificada(alerta_info["alerta_id"])
        
        # Agregar información de alerta a la respuesta
        resultado["alerta_info"] = alerta_info

        return JSONResponse(content=resultado)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------
# ENDPOINT: LISTAR TODAS LAS INSPECCIONES
# ---------------------------------------------------------

@app.get("/api/registros")
def obtener_registros():
    """
    Lista todas las inspecciones guardadas en MySQL.
    """
    registros = listar_inspecciones()

    respuesta = []
    for r in registros:
        respuesta.append({
            "id": r.id,
            "resultado": r.resultado,
            "max_distancia": r.max_distancia,
            "puntos_defectuosos": json.loads(r.puntos_defectuosos),
            "categoria": r.categoria,
            "fecha": r.fecha.isoformat()
        })

    return {"inspecciones": respuesta}


@app.get("/api/defectos")
def obtener_defectos_por_categoria(categoria: str = None):
    """
    Filtro de inspecciones por categoría.
    Ejemplo:
    GET /api/defectos?categoria=Corte%20incompleto

    - Si se pasa 'categoria', filtra por esa categoría.
    - Si no se pasa, devuelve todas las inspecciones.
    """

    if categoria:
        registros = filtrar_por_categoria(categoria)
    else:
        registros = listar_inspecciones()

    respuesta = []
    for r in registros:
        respuesta.append({
            "id": r.id,
            "resultado": r.resultado,
            "categoria": r.categoria,
            "max_distancia": r.max_distancia,
            "puntos_defectuosos": json.loads(r.puntos_defectuosos),
            "fecha": r.fecha.isoformat()
        })

    # 👇 Aquí viene la mejora para cuando no hay datos
    if not respuesta:
        mensaje = (
            f"No se encontraron inspecciones para la categoría '{categoria}'."
            if categoria
            else "No se encontraron inspecciones registradas."
        )
        return {
            "inspecciones": [],
            "total": 0,
            "mensaje": mensaje
        }

    # Si sí hay resultados, devolvemos también el total
    return {
        "inspecciones": respuesta,
        "total": len(respuesta)
    }


@app.get("/api/estadisticas/categorias")
def estadisticas_categorias():
    """
    Devuelve la cantidad de defectos agrupados por categoría.
    Ideal para gráficos en Angular.
    """
    stats = obtener_estadisticas_por_categoria()
    return {"estadisticas": stats}


# ---------------------------------------------------------
# NUEVOS ENDPOINTS: SISTEMA DE ALERTAS
# ---------------------------------------------------------

@app.get("/api/alertas/estadisticas")
def obtener_estadisticas():
    """
    Obtiene estadísticas actuales de calidad y porcentaje de defectos.
    """
    try:
        stats = AlertService.calcular_porcentaje_defectos()
        # Si hay un error en el diccionario de respuesta, lanzar excepción
        if "error" in stats:
            raise HTTPException(status_code=500, detail=stats.get("error", "Error desconocido"))
        return JSONResponse(content=stats)
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_detail = f"{str(e)}\n{traceback.format_exc()}"
        print(f"[ERROR] Error en obtener_estadisticas: {error_detail}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/alertas/historial")
def obtener_historial_alertas(limite: int = 50):
    """
    Obtiene el historial de alertas registradas.
    
    Args:
        limite: Número máximo de alertas a retornar (por defecto 50)
    """
    try:
        historial = AlertService.obtener_historial_alertas(limite=limite)
        return JSONResponse(content={"alertas": historial})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/alertas/verificar")
def verificar_alertas_manual():
    """
    Verifica manualmente si se debe crear una alerta (útil para pruebas).
    """
    try:
        alerta_info = AlertService.verificar_y_crear_alerta()
        
        # Si se creó una alerta, enviar notificación
        if alerta_info.get("alerta_creada"):
            stats = alerta_info["estadisticas"]
            email_enviado = EmailService.enviar_alerta_defectos(
                porcentaje=stats["porcentaje_defectos"],
                total_inspecciones=stats["total_inspecciones"],
                total_rechazados=stats["total_rechazados"],
                recomendacion=alerta_info["recomendacion"]
            )
            
            if email_enviado:
                AlertService.marcar_alerta_como_notificada(alerta_info["alerta_id"])
        
        return JSONResponse(content=alerta_info)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/alertas/test-email")
def probar_email():
    """
    Envía un email de prueba para verificar la configuración SMTP.
    """
    try:
        exito = EmailService.enviar_alerta_defectos(
            porcentaje=15.5,
            total_inspecciones=100,
            total_rechazados=15,
            recomendacion="Esta es una prueba del sistema de alertas."
        )
        
        if exito:
            return JSONResponse(content={
                "success": True,
                "mensaje": "Email de prueba enviado correctamente"
            })
        else:
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "mensaje": "Error al enviar email de prueba"
                }
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------
# HEALTH CHECK
# ---------------------------------------------------------

@app.get("/")
def health_check():
    """Endpoint para verificar que el servidor está funcionando."""
    return {
        "status": "online",
        "servicio": "Sistema de Control de Calidad Láser",
        "version": "2.0"
    }


# ---------------------------------------------------------
# EJECUCIÓN MANUAL (opcional)
# ---------------------------------------------------------

@app.post("/api/clasificar-defecto")
def clasificar_defecto_api(datos: DatosClasificacion):
    """
    Nueva HU: Clasificación de defectos SIN tocar la detección anterior.
    """

    nuevo = guardar_inspeccion_clasificada(
        resultado="CLASIFICADO",          # Etiqueta general
        max_distancia=0,                  # No aplica aquí, pero tu modelo lo pide
        puntos_defectuosos=[],            # No aplica, pero el modelo lo exige
        descripcion=datos.descripcion,
        color_borde=datos.color_borde,
        caracteristica_borde=datos.caracteristica_borde,
        profundidad_corte=datos.profundidad_corte,
        espesor_material=datos.espesor_material,
        dimension_fuera_rango=datos.dimension_fuera_rango,
        falla_maquina=datos.falla_maquina,
        desalineado=datos.desalineado,
        deformacion_material=datos.deformacion_material
    )

    return {
        "id": nuevo.id,
        "categoria": nuevo.categoria,
        "fecha": nuevo.fecha.isoformat()
    }


@app.get("/api/inspecciones/completas")
def obtener_inspecciones_completas():
    registros = listar_inspecciones()

    respuesta = []
    for r in registros:
        respuesta.append({
            "id": r.id,
            "resultado": r.resultado,
            "categoria": r.categoria,
            "max_distancia": r.max_distancia,
            "puntos_defectuosos": json.loads(r.puntos_defectuosos),
            "fecha": r.fecha.isoformat()
        })

    return {
        "total": len(respuesta),
        "inspecciones": respuesta
    }

@app.get("/api/exportar")
def exportar_inspecciones():
    """
    Exporta todas las inspecciones a un CSV descargable.
    """
    registros = listar_inspecciones()  # 👈 ya tienes esta función importada

    output = StringIO()
    writer = csv.writer(output)

    # Cabeceras del CSV
    writer.writerow(["ID", "Resultado", "Categoria", "Max Distancia", "Fecha"])

    # Filas
    for r in registros:
        writer.writerow([
            r.id,
            r.resultado,
            r.categoria,
            r.max_distancia,
            r.fecha.isoformat()
        ])

    output.seek(0)

    return StreamingResponse(
        output,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=inspecciones.csv"}
    )

@app.delete("/api/inspecciones/{id}")
def eliminar_inspeccion_api(id: int = Path(...)):
    """
    Elimina una inspección por ID.
    """
    resultado = eliminar_inspeccion(id)

    if resultado is None:
        return {"mensaje": "Inspección no encontrada"}

    return {"mensaje": "Inspección eliminada correctamente"}


@app.post("/api/lotes")
def api_crear_lote(datos: DatosLote):
    nuevo = crear_lote(
        codigo_lote=datos.codigo_lote,
        inspector=datos.inspector,
        cliente=datos.cliente,
        tipo_producto=datos.tipo_producto,
        orden=datos.orden
    )
    return {
        "id": nuevo.id,
        "codigo_lote": nuevo.codigo_lote,
        "inspector": nuevo.inspector,
        "estado": nuevo.estado,
        "fecha": nuevo.fecha.isoformat(),
        "cliente": nuevo.cliente,
        "tipo_producto": nuevo.tipo_producto,
        "orden": nuevo.orden
    }

@app.get("/api/lotes/listar")
def api_listar_lotes():
    lotes = listar_lotes()

    respuesta = []
    for l in lotes:
        respuesta.append({
            "id": l.id,
            "codigo_lote": l.codigo_lote,
            "inspector": l.inspector,
            "estado": l.estado,
            "fecha": l.fecha.isoformat(),
            "total_inspecciones": len(l.inspecciones)
        })

    return {"lotes": respuesta}

@app.get("/api/lotes/{id_lote}")
def api_obtener_lote(id_lote: int):
    lote = obtener_lote(id_lote)

    if not lote:
        raise HTTPException(status_code=404, detail="Lote no encontrado")

    inspecciones = []
    for ins in lote.inspecciones:
        inspecciones.append({
            "id": ins.id,
            "resultado": ins.resultado,
            "categoria": ins.categoria,
            "max_distancia": ins.max_distancia,
            "fecha": ins.fecha.isoformat()
        })

    return {
        "id": lote.id,
        "codigo_lote": lote.codigo_lote,
        "inspector": lote.inspector,
        "estado": lote.estado,
        "fecha": lote.fecha.isoformat(),
        "inspecciones": inspecciones
    }

@app.post("/api/lotes/{id_lote}/agregar-inspeccion")
def api_agregar_inspeccion(id_lote: int, datos: DatosAgregarInspeccion):
    asociada = agregar_inspeccion_a_lote(id_lote, datos.id_inspeccion)

    if not asociada:
        raise HTTPException(
            status_code=400,
            detail="No se pudo asociar la inspección al lote."
        )

    return {
        "mensaje": "Inspección agregada al lote correctamente",
        "inspeccion_id": asociada.id,
        "lote_id": asociada.lote_id
    }

from modules.crud_lotes import crear_lote, listar_lotes, obtener_lote, agregar_inspeccion_a_lote
# 👆 ese import ya lo tienes, mantenlo

from modules.crud import listar_inspecciones  # ya lo tienes arriba


@app.get("/api/lotes/{id_lote}/exportar")
def exportar_lote(id_lote: int):
    """
    Exporta a CSV todas las inspecciones asociadas a un lote específico.
    """
    lote = obtener_lote(id_lote)

    if not lote:
        raise HTTPException(status_code=404, detail="Lote no encontrado")

    if not lote.inspecciones:
        raise HTTPException(status_code=404, detail="Ese lote no tiene inspecciones asociadas")

    output = StringIO()
    writer = csv.writer(output)

    # Cabeceras del CSV
    writer.writerow(["ID Inspección", "Resultado", "Categoria", "Max Distancia", "Fecha"])

    # Filas: todas las inspecciones del lote
    for ins in lote.inspecciones:
        writer.writerow([
            ins.id,
            ins.resultado,
            ins.categoria,
            ins.max_distancia,
            ins.fecha.isoformat()
        ])

    output.seek(0)

    return StreamingResponse(
        output,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=lote_{id_lote}.csv"}
    )


# ---------------------------------------------------------
# NUEVOS ENDPOINTS: HISTORIAL DE CALIDAD POR CLIENTE
# ---------------------------------------------------------

@app.get("/api/historial-calidad")
def obtener_historial_calidad(
    cliente: Optional[str] = None,
    fecha_inicio: Optional[str] = None,  # Formato: YYYY-MM-DD
    fecha_fin: Optional[str] = None,  # Formato: YYYY-MM-DD
    tipo_producto: Optional[str] = None,
    estado: Optional[str] = None,
    pagina: int = 1,
    por_pagina: int = 20,
    orden: str = "desc",  # 'desc' o 'asc'
    usuario: Optional[str] = None  # Para auditoría
):
    """
    Consulta el historial de calidad por cliente con filtros y paginación.
    
    Filtros disponibles:
    - cliente: Nombre del cliente (búsqueda parcial)
    - fecha_inicio: Fecha de inicio (YYYY-MM-DD)
    - fecha_fin: Fecha de fin (YYYY-MM-DD)
    - tipo_producto: Tipo de producto (búsqueda parcial)
    - estado: Estado del producto o inspección (búsqueda parcial)
    - pagina: Número de página (por defecto 1)
    - por_pagina: Registros por página (por defecto 20)
    - orden: 'desc' (más reciente primero) o 'asc' (más antiguo primero)
    - usuario: Usuario que realiza la consulta (para auditoría)
    """
    try:
        # Convertir fechas de string a datetime
        fecha_inicio_dt = None
        fecha_fin_dt = None
        
        if fecha_inicio:
            try:
                fecha_inicio_dt = datetime.strptime(fecha_inicio, "%Y-%m-%d")
            except ValueError:
                raise HTTPException(status_code=400, detail="Formato de fecha_inicio inválido. Use YYYY-MM-DD")
        
        if fecha_fin:
            try:
                fecha_fin_dt = datetime.strptime(fecha_fin, "%Y-%m-%d")
            except ValueError:
                raise HTTPException(status_code=400, detail="Formato de fecha_fin inválido. Use YYYY-MM-DD")
        
        # Validar paginación
        if pagina < 1:
            pagina = 1
        if por_pagina < 1 or por_pagina > 100:
            por_pagina = 20
        
        # Consultar historial
        resultado = consultar_historial_calidad(
            cliente=cliente,
            fecha_inicio=fecha_inicio_dt,
            fecha_fin=fecha_fin_dt,
            tipo_producto=tipo_producto,
            estado=estado,
            pagina=pagina,
            por_pagina=por_pagina,
            orden=orden
        )
        
        # Registrar auditoría de consulta
        if usuario:
            registrar_auditoria(
                tipo_accion="CONSULTA",
                usuario=usuario,
                cliente=cliente,
                fecha_inicio=fecha_inicio_dt,
                fecha_fin=fecha_fin_dt,
                tipo_producto=tipo_producto,
                estado=estado
            )
        
        # Si no hay resultados, devolver mensaje apropiado
        if resultado["paginacion"]["total_registros"] == 0:
            mensaje = "No se encontraron resultados para el criterio seleccionado."
            if cliente or fecha_inicio or fecha_fin or tipo_producto or estado:
                mensaje += " Puede limpiar los filtros o cambiar el rango de fechas."
            
            return JSONResponse(content={
                "registros": [],
                "paginacion": resultado["paginacion"],
                "mensaje": mensaje
            })
        
        return JSONResponse(content=resultado)
    
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_detail = f"{str(e)}\n{traceback.format_exc()}"
        print(f"[ERROR] Error en obtener_historial_calidad: {error_detail}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/historial-calidad/exportar-pdf")
def exportar_historial_pdf(
    cliente: Optional[str] = None,
    fecha_inicio: Optional[str] = None,
    fecha_fin: Optional[str] = None,
    tipo_producto: Optional[str] = None,
    estado: Optional[str] = None,
    usuario: Optional[str] = None
):
    """
    Exporta el historial de calidad a PDF con los filtros aplicados.
    """
    try:
        # Convertir fechas
        fecha_inicio_dt = None
        fecha_fin_dt = None
        
        if fecha_inicio:
            fecha_inicio_dt = datetime.strptime(fecha_inicio, "%Y-%m-%d")
        if fecha_fin:
            fecha_fin_dt = datetime.strptime(fecha_fin, "%Y-%m-%d")
        
        # Obtener todos los registros (sin paginación)
        registros = obtener_historial_completo_para_exportacion(
            cliente=cliente,
            fecha_inicio=fecha_inicio_dt,
            fecha_fin=fecha_fin_dt,
            tipo_producto=tipo_producto,
            estado=estado
        )
        
        # Generar PDF
        pdf_buffer = generar_pdf_historial(
            registros=registros,
            cliente=cliente,
            fecha_inicio=fecha_inicio_dt,
            fecha_fin=fecha_fin_dt,
            usuario=usuario
        )
        
        # Registrar auditoría de descarga
        if usuario:
            registrar_auditoria(
                tipo_accion="DESCARGA",
                usuario=usuario,
                cliente=cliente,
                fecha_inicio=fecha_inicio_dt,
                fecha_fin=fecha_fin_dt,
                tipo_producto=tipo_producto,
                estado=estado,
                formato_exportacion="PDF"
            )
        
        # Generar nombre de archivo
        nombre_archivo = f"historial_calidad_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        if cliente:
            nombre_archivo = f"historial_calidad_{cliente.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        return StreamingResponse(
            pdf_buffer,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={nombre_archivo}"}
        )
    
    except Exception as e:
        import traceback
        error_detail = f"{str(e)}\n{traceback.format_exc()}"
        print(f"[ERROR] Error en exportar_historial_pdf: {error_detail}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/historial-calidad/exportar-excel")
def exportar_historial_excel(
    cliente: Optional[str] = None,
    fecha_inicio: Optional[str] = None,
    fecha_fin: Optional[str] = None,
    tipo_producto: Optional[str] = None,
    estado: Optional[str] = None,
    usuario: Optional[str] = None
):
    """
    Exporta el historial de calidad a Excel con los filtros aplicados.
    """
    try:
        # Convertir fechas
        fecha_inicio_dt = None
        fecha_fin_dt = None
        
        if fecha_inicio:
            fecha_inicio_dt = datetime.strptime(fecha_inicio, "%Y-%m-%d")
        if fecha_fin:
            fecha_fin_dt = datetime.strptime(fecha_fin, "%Y-%m-%d")
        
        # Obtener todos los registros (sin paginación)
        registros = obtener_historial_completo_para_exportacion(
            cliente=cliente,
            fecha_inicio=fecha_inicio_dt,
            fecha_fin=fecha_fin_dt,
            tipo_producto=tipo_producto,
            estado=estado
        )
        
        # Generar Excel
        excel_buffer = generar_excel_historial(
            registros=registros,
            cliente=cliente,
            fecha_inicio=fecha_inicio_dt,
            fecha_fin=fecha_fin_dt,
            usuario=usuario
        )
        
        # Registrar auditoría de descarga
        if usuario:
            registrar_auditoria(
                tipo_accion="DESCARGA",
                usuario=usuario,
                cliente=cliente,
                fecha_inicio=fecha_inicio_dt,
                fecha_fin=fecha_fin_dt,
                tipo_producto=tipo_producto,
                estado=estado,
                formato_exportacion="EXCEL"
            )
        
        # Generar nombre de archivo
        nombre_archivo = f"historial_calidad_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        if cliente:
            nombre_archivo = f"historial_calidad_{cliente.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        return StreamingResponse(
            excel_buffer,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={nombre_archivo}"}
        )
    
    except Exception as e:
        import traceback
        error_detail = f"{str(e)}\n{traceback.format_exc()}"
        print(f"[ERROR] Error en exportar_historial_excel: {error_detail}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)


