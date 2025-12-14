-- ============================================
-- QUERIES SQL PARA CREAR TABLAS EN MYSQL
-- ============================================
-- Ejecuta estas queries en tu base de datos MySQL
-- Base de datos: telas_sublimadas
-- ============================================

-- Seleccionar la base de datos
USE telas_sublimadas;

-- ============================================
-- TABLA: lotes
-- ============================================
CREATE TABLE IF NOT EXISTS lotes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    codigo_lote VARCHAR(30) NOT NULL UNIQUE,
    inspector VARCHAR(100),
    estado VARCHAR(20) DEFAULT 'EN PROCESO',
    fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
    cliente VARCHAR(100),
    tipo_producto VARCHAR(50),
    orden VARCHAR(50),
    INDEX idx_codigo_lote (codigo_lote),
    INDEX idx_cliente (cliente),
    INDEX idx_tipo_producto (tipo_producto)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- TABLA: inspecciones
-- ============================================
CREATE TABLE IF NOT EXISTS inspecciones (
    id INT AUTO_INCREMENT PRIMARY KEY,
    resultado VARCHAR(20),
    max_distancia FLOAT,
    puntos_defectuosos TEXT,
    categoria VARCHAR(50) DEFAULT 'Excluido',
    fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
    observaciones TEXT,
    lote_id INT NULL,
    INDEX idx_categoria (categoria),
    INDEX idx_fecha (fecha),
    INDEX idx_lote_id (lote_id),
    FOREIGN KEY (lote_id) REFERENCES lotes(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- TABLA: alertas
-- ============================================
CREATE TABLE IF NOT EXISTS alertas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    tipo_alerta VARCHAR(50),
    porcentaje_defectos FLOAT,
    total_inspecciones INT,
    total_rechazados INT,
    umbral_configurado FLOAT,
    recomendacion TEXT,
    notificacion_enviada BOOLEAN DEFAULT FALSE,
    fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_fecha (fecha),
    INDEX idx_tipo_alerta (tipo_alerta)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- TABLA: auditoria
-- ============================================
CREATE TABLE IF NOT EXISTS auditoria (
    id INT AUTO_INCREMENT PRIMARY KEY,
    tipo_accion VARCHAR(50),
    usuario VARCHAR(100),
    cliente VARCHAR(100),
    fecha_inicio DATETIME NULL,
    fecha_fin DATETIME NULL,
    tipo_producto VARCHAR(50),
    estado VARCHAR(20),
    formato_exportacion VARCHAR(10),
    parametros_busqueda TEXT,
    fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_tipo_accion (tipo_accion),
    INDEX idx_usuario (usuario),
    INDEX idx_cliente (cliente),
    INDEX idx_fecha (fecha)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- VERIFICACIÓN: Mostrar las tablas creadas
-- ============================================
SHOW TABLES;

-- ============================================
-- VERIFICACIÓN: Mostrar estructura de tablas
-- ============================================
DESCRIBE lotes;
DESCRIBE inspecciones;
DESCRIBE alertas;
DESCRIBE auditoria;

-- ============================================
-- MIGRACIÓN: Agregar nuevos campos a tablas existentes
-- ============================================
-- Si las tablas ya existen, ejecuta estos ALTER TABLE:

-- Agregar campos a tabla lotes (si no existen)
ALTER TABLE lotes 
ADD COLUMN IF NOT EXISTS cliente VARCHAR(100),
ADD COLUMN IF NOT EXISTS tipo_producto VARCHAR(50),
ADD COLUMN IF NOT EXISTS orden VARCHAR(50);

-- Agregar índices a tabla lotes (si no existen)
CREATE INDEX IF NOT EXISTS idx_cliente ON lotes(cliente);
CREATE INDEX IF NOT EXISTS idx_tipo_producto ON lotes(tipo_producto);

-- Agregar campo observaciones a tabla inspecciones (si no existe)
ALTER TABLE inspecciones 
ADD COLUMN IF NOT EXISTS observaciones TEXT;
