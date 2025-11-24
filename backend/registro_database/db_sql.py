import sqlite3

# Conectar (si no existe la base, la crea)
conn = sqlite3.connect("registro_defectos.db")
cursor = conn.cursor()

# Crear tabla si no existe
cursor.execute("""
CREATE TABLE IF NOT EXISTS registro_defectos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lote TEXT NOT NULL,
    pieza INTEGER NOT NULL,
    defecto TEXT NOT NULL,
    severidad TEXT NOT NULL,
    confianza REAL NOT NULL,
    fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
    inspector TEXT DEFAULT 'Sistema'
)
""")

conn.commit()

# Mostrar tablas existentes
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
print(cursor.fetchall())

conn.close()
