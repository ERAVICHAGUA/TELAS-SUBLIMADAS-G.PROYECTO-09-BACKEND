import sqlite3

conn = sqlite3.connect("registro_defectos.db")
cursor = conn.cursor()

cursor.execute("SELECT * FROM registro_defectos")
rows = cursor.fetchall()

for row in rows:
    print(row)

conn.close()
