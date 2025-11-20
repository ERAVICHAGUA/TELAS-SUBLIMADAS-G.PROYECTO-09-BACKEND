import cv2
import numpy as np
import os

# ============================================================
#  RUTAS Y CONSTANTES
# ============================================================

# Ruta real de este archivo → backend/modules/
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

# Ruta hacia la carpeta backend/
BACKEND_DIR = os.path.abspath(os.path.join(CURRENT_DIR, '..'))

# Ruta al archivo plantilla_ideal.png (está dentro de backend/)
PLANTILLA_PATH = os.path.join(BACKEND_DIR, 'plantilla_ideal.png')

TOLERANCIA_MAXIMA = 2
CONTORNO_IDEAL = None

print("==============================================")
print("🔧 CONFIGURANDO ANALISIS.PY")
print("Ruta actual del archivo:", CURRENT_DIR)
print("Ruta de backend:", BACKEND_DIR)
print("Ruta final de plantilla:", PLANTILLA_PATH)
print("==============================================")


# ============================================================
#  CARGA DE PLANTILLA IDEAL
# ============================================================

def cargar_contorno_ideal():
    """Carga la plantilla y extrae su contorno perfecto."""
    global CONTORNO_IDEAL

    print("🔍 Intentando cargar la plantilla ideal desde:")
    print("➡", PLANTILLA_PATH)

    # 1. Leer imagen
    img = cv2.imread(PLANTILLA_PATH, cv2.IMREAD_GRAYSCALE)

    if img is None:
        print("❌ ERROR: No se pudo cargar la plantilla ideal desde esa ruta.")
        return False

    print("✔ Imagen cargada correctamente.")

    # 2. Umbralización (sin blur)
    _, thresh_ideal = cv2.threshold(img, 50, 255, cv2.THRESH_BINARY)

    # 3. Buscar contornos
    contornos_ideal, _ = cv2.findContours(
        thresh_ideal, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )

    if not contornos_ideal:
        print("❌ ERROR: No se detectaron contornos en la plantilla ideal.")
        return False

    # 4. Guardamos el contorno más grande
    CONTORNO_IDEAL = max(contornos_ideal, key=cv2.contourArea)

    print("✔ Contorno ideal cargado correctamente.")
    print("==============================================")
    return True



# ============================================================
#  FUNCIÓN PRINCIPAL DE ANÁLISIS
# ============================================================

def analizar_molde(imagen_bytes: bytes):
    """Compara la imagen real contra la plantilla ideal."""
    if CONTORNO_IDEAL is None:
        return {"status": "ERROR", "mensaje": "La plantilla ideal no está cargada."}

    try:
        # Decodificar imagen
        nparr = np.frombuffer(imagen_bytes, np.uint8)
        imagen_real = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)

        if imagen_real is None:
            return {"status": "ERROR", "mensaje": "No se pudo decodificar la imagen."}

        # 1. Umbralización
        _, thresh = cv2.threshold(imagen_real, 50, 255, cv2.THRESH_BINARY)

        # 2. Contornos reales
        contornos_real, _ = cv2.findContours(
            thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        if not contornos_real:
            return {"status": "ERROR", "mensaje": "No se detectó ningún contorno."}

        contorno_real = max(contornos_real, key=cv2.contourArea)

        # 3. Comparación punto a punto (CORRECCIÓN: usar distancia negativa para puntos fuera)
        defectos = []
        max_dist = 0.0

        for punto in contorno_real:
            x, y = punto[0]

            distancia = cv2.pointPolygonTest(CONTORNO_IDEAL, (float(x), float(y)), True)
            # Si la distancia es negativa, el punto está fuera del contorno ideal.
            # Tomamos el valor absoluto para reportar magnitud del defecto.
            if distancia < -TOLERANCIA_MAXIMA:
                defectos.append([int(x), int(y)])
                if abs(distancia) > max_dist:
                    max_dist = abs(distancia)

        # 4. Resultado
        if defectos:
            return {
                "status": "RECHAZADO",
                "mensaje": f"❌ Rebaba detectada. Distancia máx: {max_dist:.2f}px",
                "puntos_defectuosos": defectos,
                "max_distancia": float(max_dist),
            }
        else:
            return {
                "status": "APROBADO",
                "mensaje": "✔ Molde sin rebabas.",
                "puntos_defectuosos": [],
                "max_distancia": 0.0,
            }

    except Exception as e:
        return {
            "status": "ERROR",
            "mensaje": f"Error durante el análisis: {str(e)}"
        }
