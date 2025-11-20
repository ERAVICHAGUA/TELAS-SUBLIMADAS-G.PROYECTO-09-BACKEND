# generate_assets.py
import cv2
import numpy as np
import os

# --- Parámetros de la Imagen ---
IMG_SIZE = 600       # 600x600 píxeles
MOLD_SIZE = 300      # 300x300 píxeles para el molde central
REBABA_SIZE = 10     # Tamaño del defecto que queremos detectar

# Colores (OpenCV usa BGR para 3 canales, pero aquí usamos 1 canal GRAYSCALE)
BLACK = 0    # Fondo
WHITE = 255  # Molde

def crear_molde_base():
    """Crea una imagen de fondo negro con un cuadrado blanco centrado."""
    # Crea una imagen completamente negra (600x600)
    imagen = np.zeros((IMG_SIZE, IMG_SIZE), dtype=np.uint8) 
    
    # Coordenadas del molde centrado
    start = (IMG_SIZE - MOLD_SIZE) // 2
    end = start + MOLD_SIZE
    
    # Dibuja el cuadrado blanco en el centro
    imagen[start:end, start:end] = WHITE
    return imagen

def generar_plantilla_ideal():
    """Genera la plantilla perfecta."""
    img = crear_molde_base()
    cv2.imwrite('plantilla_ideal.png', img)
    print("✅ Generada: plantilla_ideal.png")

def generar_molde_ok():
    """Genera una copia perfecta."""
    img = crear_molde_base()
    cv2.imwrite('molde_ok.png', img)
    print("✅ Generada: molde_ok.png")

def generar_molde_rebaba():
    """
    Genera la imagen con un defecto (rebaba) de tamaño REBABA_SIZE.
    Esto garantiza que el algoritmo lo detecte.
    """
    img = crear_molde_base()
    
    # --- Añadir el Defecto ---
    
    # Coordenadas donde empieza el molde blanco
    start = (IMG_SIZE - MOLD_SIZE) // 2 
    
    # Ubicación del defecto (ej. en el lado derecho, en el centro vertical)
    rebaba_x = start + MOLD_SIZE # Borde derecho
    rebaba_y_start = IMG_SIZE // 2 - (REBABA_SIZE // 2) # Centro vertical
    rebaba_y_end = rebaba_y_start + REBABA_SIZE
    
    # Dibuja la rebaba (un rectángulo que sobresale 10px)
    # Sobresale del borde derecho del cuadrado
    img[rebaba_y_start:rebaba_y_end, rebaba_x:rebaba_x + REBABA_SIZE] = WHITE
    
    cv2.imwrite('molde_rebaba.png', img)
    print(f"✅ Generada: molde_rebaba.png (Defecto de {REBABA_SIZE}px garantizado)")


if __name__ == '__main__':
    print("--- Generando Assets de Prueba ---")
    generar_plantilla_ideal()
    generar_molde_ok()
    generar_molde_rebaba()
    print("--- Proceso Completo ---")