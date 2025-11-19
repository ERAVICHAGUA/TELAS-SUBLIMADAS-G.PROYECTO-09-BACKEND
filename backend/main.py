# backend/main.py
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
import uvicorn
# Importamos la lógica de análisis del módulo
from modules.analisis import analizar_molde, cargar_contorno_ideal

app = FastAPI(
    title="Sistema de Control de Calidad Láser (Simulación)",
    description="Backend de FastAPI modular para detección de rebaba."
)

# --- Evento de Inicio (Carga la plantilla ANTES de que se ejecute la API) ---
@app.on_event("startup")
def startup_event():
    """Intenta cargar el contorno de la plantilla ideal al iniciar el servidor."""
    if not cargar_contorno_ideal():
        # Si falla al cargar la plantilla, se registra el error, pero el servidor puede seguir
        print("ADVERTENCIA: Falló la carga de la plantilla ideal. La API de inspección no funcionará.")

# --- Endpoint para la Historia de Usuario: Detección de Bordes ---
@app.post("/api/inspeccionar")
async def inspeccionar_calidad(file: UploadFile = File(...)):
    """
    Recibe la imagen del molde cortado y determina si hay rebaba.
    Llama a la lógica central en el módulo 'analisis'.
    """
    try:
        # Leer el contenido binario del archivo
        imagen_bytes = await file.read()
        
        # Llamar a la función de análisis
        resultado = analizar_molde(imagen_bytes)
        
        # Manejo de error de dimensiones o decodificación
        if resultado.get("status") == "ERROR":
            raise HTTPException(status_code=400, detail=resultado["mensaje"])
            
        return JSONResponse(content=resultado)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    # Comando de ejecución manual si no usas uvicorn main:app
    uvicorn.run(app, host="0.0.0.0", port=8000)