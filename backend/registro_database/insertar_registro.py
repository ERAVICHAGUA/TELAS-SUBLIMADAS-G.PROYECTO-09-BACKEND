import sqlite3

conn = sqlite3.connect("registro_defectos.db")
cursor = conn.cursor()

registro = {
    "lote": "L2025-01",
    "pieza": 15,
    "defecto": "rebaba",
    "severidad": "alta",
    "confianza": 0.92,
    "inspector": "QA_TEST"
}

cursor.execute("""
INSERT INTO registro_defectos (lote, pieza, defecto, severidad, confianza, inspector)
VALUES (:lote, :pieza, :defecto, :severidad, :confianza, :inspector)
""", registro)

conn.commit()
conn.close()
print("Registro insertado correctamente.")
