# Configuración de MySQL

Este proyecto ahora utiliza MySQL en lugar de SQLite. Sigue estos pasos para configurarlo:

## 1. Instalar MySQL

Asegúrate de tener MySQL instalado y corriendo en tu máquina local.

## 2. Crear la Base de Datos

Ejecuta el siguiente comando en MySQL para crear la base de datos:

```sql
CREATE DATABASE telas_sublimadas CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

## 3. Configurar Variables de Entorno

Crea un archivo `.env` en la carpeta `backend/` con las siguientes variables:

```env
# ============================================
# CONFIGURACIÓN DE BASE DE DATOS MYSQL
# ============================================
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=tu_contraseña_mysql
DB_NAME=telas_sublimadas

# ============================================
# CONFIGURACIÓN SMTP (Email)
# ============================================
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=tu_email@gmail.com
SMTP_PASS=tu_contraseña_app
FROM_EMAIL=tu_email@gmail.com
ALERT_EMAIL=destinatario@example.com

# ============================================
# CONFIGURACIÓN DE ALERTAS
# ============================================
ALERT_THRESHOLD=5.0
CALCULATION_WINDOW=100
```

**Importante:** Reemplaza los valores con tus credenciales reales de MySQL.

## 4. Instalar Dependencias

Instala las nuevas dependencias (incluye pymysql):

```bash
cd backend
pip install -r requirements.txt
```

## 5. Ejecutar el Proyecto

Al ejecutar el proyecto, las tablas se crearán automáticamente en MySQL:

```bash
python main.py
```

O usando uvicorn directamente:

```bash
uvicorn main:app --reload
```

## Notas

- El proyecto creará automáticamente las tablas necesarias al iniciar.
- Asegúrate de que MySQL esté corriendo antes de iniciar el backend.
- Si cambias la contraseña o configuración de MySQL, actualiza el archivo `.env`.
