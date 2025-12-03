# backend/modules/rules_clasificacion.py
from typing import Literal, Dict, Any

CategoriaNombre = Literal[
    "Corte incompleto",
    "Sobrecalentamiento",
    "Borde irregular",
    "Desalineación",
    "Dimensión incorrecta",
    "Deformación por calor",
    "Error de máquina",
    "Excluido",
]


def clasificar_defecto(data: Dict[str, Any]) -> CategoriaNombre:
    """
    Recibe un diccionario con la info del defecto
    y devuelve el nombre de la categoría.

    OJO: aquí debes usar los campos que tu profe les explicó
    como input (profundidad, grosor, etc.). Por ahora
    te dejo un ejemplo basado en corte láser.
    """

    desc = (data.get("descripcion") or "").lower()
    color = (data.get("color_borde") or "").lower()
    borde = (data.get("caracteristica_borde") or "").lower()
    profundidad = data.get("profundidad_corte")
    espesor = data.get("espesor_material")
    dimension_fuera_rango = bool(data.get("dimension_fuera_rango"))
    falla_maquina = bool(data.get("falla_maquina"))
    desalineado = bool(data.get("desalineado"))
    deformacion_material = bool(data.get("deformacion_material"))

    # Regla 1: Corte incompleto
    if profundidad is not None and espesor is not None and profundidad < espesor:
        return "Corte incompleto"

    # Regla 2: Sobrecalentamiento
    if ("quemad" in desc) or ("carboniz" in desc) or (color == "oscuro"):
        return "Sobrecalentamiento"

    # Regla 3: Borde irregular
    if ("irregular" in borde) or ("rebaba" in borde) or ("pelosidad" in borde):
        return "Borde irregular"

    # Regla 4: Desalineación
    if desalineado:
        return "Desalineación"

    # Regla 5: Dimensión incorrecta
    if dimension_fuera_rango:
        return "Dimensión incorrecta"

    # Regla 6: Deformación por calor
    if deformacion_material:
        return "Deformación por calor"

    # Regla 7: Error de máquina
    if falla_maquina:
        return "Error de máquina"

    # Regla 8: Excluido (ninguna regla aplica)
    return "Excluido"
