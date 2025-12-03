# backend/main.py
import csv
from io import StringIO
from fastapi.responses import StreamingResponse
from modules.crud import eliminar_inspeccion
from fastapi import Path


from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
import uvicorn
import json
from modules.db import Base, engine
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

class DatosAgregarInspeccion(BaseModel):
    id_inspeccion: int

# ---------------------------------------------------------
# CONFIG FASTAPI
# ---------------------------------------------------------

app = FastAPI(
    title="Sistema de Control de Calidad Láser (Simulación)",
    description="Backend de FastAPI modular para detección de rebaba y registro de inspecciones."
)

# ---------------------------------------------------------
# EVENTO DE INICIO: CARGA DE PLANTILLA IDEAL
# ---------------------------------------------------------

@app.on_event("startup")
def startup_event():
    """Carga la plantilla ideal y crea la base de datos si no existe."""
    
    # Crear tablas de SQLite
    Base.metadata.create_all(bind=engine)
    print("✔ Base de datos lista. Tablas creadas.")
    
    # Cargar plantilla ideal
    if not cargar_contorno_ideal():
        print("⚠ ADVERTENCIA: No se cargó la plantilla ideal. El análisis no funcionará.")


# ---------------------------------------------------------
# ENDPOINT PRINCIPAL: INSPECCIÓN DE MOLDE
# ---------------------------------------------------------

@app.post("/api/inspeccionar")
async def inspeccionar_calidad(file: UploadFile = File(...)):
    """
    Recibe la imagen y devuelve si está APROBADA o RECHAZADA.
    Además guarda el resultado en SQLite.
    """
    try:
        # Leer bytes de la imagen
        imagen_bytes = await file.read()

        # Ejecutar análisis
        resultado = analizar_molde(imagen_bytes)

        # Validación de errores
        if resultado.get("status") == "ERROR":
            raise HTTPException(status_code=400, detail=resultado["mensaje"])

        # Guardar resultado en SQLite
        guardar_inspeccion(
            resultado=resultado["status"],
            max_distancia=resultado["max_distancia"],
            puntos_defectuosos=resultado["puntos_defectuosos"],
        )

        return JSONResponse(content=resultado)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------
# ENDPOINT: LISTAR TODAS LAS INSPECCIONES
# ---------------------------------------------------------

@app.get("/api/registros")
def obtener_registros():
    """
    Lista todas las inspecciones guardadas en SQLite.
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
        inspector=datos.inspector
    )
    return {
        "id": nuevo.id,
        "codigo_lote": nuevo.codigo_lote,
        "inspector": nuevo.inspector,
        "estado": nuevo.estado,
        "fecha": nuevo.fecha.isoformat()
    }

@app.get("/api/lotes")
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

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
