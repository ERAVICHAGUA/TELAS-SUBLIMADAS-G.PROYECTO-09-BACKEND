# backend/modules/analisis.py
import cv2
import numpy as np
import io

# --- CONSTANTES ---
# Carga la plantilla ideal (debe estar en el directorio /backend/assets, pero lo ponemos aquí por simplicidad)
# NOTA: Por simplicidad, asumimos que 'plantilla_ideal.png' está en la misma carpeta que 'main.py'
PLANTILLA_PATH = 'plantilla_ideal.png' 
TOLERANCIA_MAXIMA = 0.5 
CONTORNO_IDEAL = None

# --- Función de Inicialización (se llama una vez al iniciar FastAPI) ---
def cargar_contorno_ideal():
    """Carga la plantilla de referencia y extrae su contorno perfecto."""
    global CONTORNO_IDEAL
    try:
        # 1. Cargar imagen
        img = cv2.imread(PLANTILLA_PATH, cv2.IMREAD_GRAYSCALE)
        if img is None:
            print(f"ERROR: No se pudo cargar la plantilla ideal desde {PLANTILLA_PATH}")
            return False
            
        # 2. Pre-procesamiento: Umbralización estricta para obtener la forma pura
        _, thresh_ideal = cv2.threshold(img, 128, 255, cv2.THRESH_BINARY)
        
        # 3. Encontrar contornos
        contornos_ideal, _ = cv2.findContours(thresh_ideal, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # 4. Asignar el contorno más grande como referencia
        if contornos_ideal:
            CONTORNO_IDEAL = max(contornos_ideal, key=cv2.contourArea)
            return True
        else:
            print("ERROR: No se detectaron contornos en la plantilla ideal.")
            return False

    except Exception as e:
        print(f"Error al configurar la plantilla ideal: {e}")
        return False

# --- Función Principal de Análisis ---
def analizar_molde(imagen_bytes: bytes):
    """
    Procesa la imagen del molde y compara su contorno con el contorno ideal.
    Devuelve un diccionario con el resultado de la inspección.
    """
    if CONTORNO_IDEAL is None:
        return {"status": "ERROR", "mensaje": "Plantilla de referencia no cargada."}

    try:
        # Decodificar la imagen de los bytes recibidos de FastAPI
        nparr = np.frombuffer(imagen_bytes, np.uint8)
        imagen_real = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)

        if imagen_real is None:
             return {"status": "ERROR", "mensaje": "Imagen subida no pudo ser decodificada."}

        # Comprobación de dimensiones (simplificación académica)
        if imagen_real.shape != CONTORNO_IDEAL.shape[:2]: # Comparar solo alto y ancho
             return {"status": "ERROR", "mensaje": "Las dimensiones no coinciden con la plantilla."}


        # 1. Pre-procesamiento de la imagen real
        imagen_blur = cv2.GaussianBlur(imagen_real, (5, 5), 0)
        _, thresh = cv2.threshold(imagen_blur, 50, 255, cv2.THRESH_BINARY) 
        
        # 2. Detección del Contorno Real
        contornos_real, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if not contornos_real:
            return {"status": "ERROR", "mensaje": "No se detectó ningún contorno en la imagen subida."}

        contorno_real = max(contornos_real, key=cv2.contourArea)

        # 3. Lógica de Evaluación (Comparación Punto a Punto)
        defectos_encontrados = False
        puntos_defectuosos = []
        max_distancia = 0

        for punto in contorno_real:
            x, y = punto[0]
            
            # Calcula la distancia del punto real al contorno ideal
            distancia = cv2.pointPolygonTest(CONTORNO_IDEAL, (float(x), float(y)), True)
            
            # Si sobresale más que la tolerancia...
            if distancia > TOLERANCIA_MAXIMA:
                defectos_encontrados = True
                puntos_defectuosos.append([int(x), int(y)])
                if distancia > max_distancia:
                    max_distancia = distancia
        
        # 4. Resultado Final
        if defectos_encontrados:
            return {
                "status": "RECHAZADO",
                "mensaje": f"🚨 RECHAZADO. Error máx: {max_distancia:.2f} px. Tolerancia: {TOLERANCIA_MAXIMA} px.",
                "puntos_defectuosos": puntos_defectuosos,
                "max_distancia": float(max_distancia)
            }
        else:
            return {
                "status": "APROBADO",
                "mensaje": "✅ APROBADO. La calidad es excelente.",
                "puntos_defectuosos": [],
                "max_distancia": 0.0
            }

    except Exception as e:
        return {"status": "ERROR", "mensaje": f"Error inesperado durante el análisis: {str(e)}"}