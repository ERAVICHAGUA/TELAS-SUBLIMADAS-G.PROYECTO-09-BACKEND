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

-- Agregar campos para mantenimiento preventivo a tabla inspecciones
ALTER TABLE inspecciones 
ADD COLUMN IF NOT EXISTS maquina VARCHAR(50),
ADD COLUMN IF NOT EXISTS turno VARCHAR(20);

-- Crear índices para mantenimiento
CREATE INDEX IF NOT EXISTS idx_inspecciones_maquina ON inspecciones(maquina);

-- ============================================
-- TABLA: eventos_mantenimiento
-- ============================================
CREATE TABLE IF NOT EXISTS eventos_mantenimiento (
    id INT AUTO_INCREMENT PRIMARY KEY,
    maquina VARCHAR(50) NOT NULL,
    tipo_evento VARCHAR(50) NOT NULL,
    fecha_hora DATETIME DEFAULT CURRENT_TIMESTAMP,
    lote_id INT NULL,
    turno VARCHAR(20),
    inspeccion_id INT NULL,
    responsable VARCHAR(100),
    estado VARCHAR(20) DEFAULT 'ABIERTA',
    orden_mantenimiento_id INT NULL,
    INDEX idx_maquina (maquina),
    INDEX idx_tipo_evento (tipo_evento),
    INDEX idx_fecha_hora (fecha_hora),
    INDEX idx_estado (estado),
    INDEX idx_lote_id (lote_id),
    INDEX idx_orden_mantenimiento_id (orden_mantenimiento_id),
    FOREIGN KEY (lote_id) REFERENCES lotes(id) ON DELETE SET NULL,
    FOREIGN KEY (inspeccion_id) REFERENCES inspecciones(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- TABLA: ordenes_mantenimiento
-- ============================================
CREATE TABLE IF NOT EXISTS ordenes_mantenimiento (
    id INT AUTO_INCREMENT PRIMARY KEY,
    maquina VARCHAR(50) NOT NULL,
    tipo_patron VARCHAR(50) NOT NULL,
    prioridad VARCHAR(20) DEFAULT 'MEDIA',
    estado VARCHAR(20) DEFAULT 'ABIERTA',
    ventana_sugerida DATETIME NULL,
    responsable VARCHAR(100),
    accion_correctiva TEXT,
    evidencia TEXT,
    fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,
    fecha_cierre DATETIME NULL,
    creado_por VARCHAR(100),
    cerrado_por VARCHAR(100),
    INDEX idx_maquina (maquina),
    INDEX idx_tipo_patron (tipo_patron),
    INDEX idx_prioridad (prioridad),
    INDEX idx_estado (estado),
    INDEX idx_fecha_creacion (fecha_creacion)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- TABLA: umbrales_alerta
-- ============================================
CREATE TABLE IF NOT EXISTS umbrales_alerta (
    id INT AUTO_INCREMENT PRIMARY KEY,
    maquina VARCHAR(50) NOT NULL,
    tipo_defecto VARCHAR(50) NOT NULL,
    umbral_eventos INT DEFAULT 3,
    ventana_tiempo_minutos INT DEFAULT 60,
    umbral_porcentaje_lote FLOAT NULL,
    activo BOOLEAN DEFAULT TRUE,
    fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_maquina (maquina),
    INDEX idx_tipo_defecto (tipo_defecto),
    INDEX idx_activo (activo),
    UNIQUE KEY unique_maquina_tipo (maquina, tipo_defecto)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- VERIFICACIÓN: Mostrar estructura de nuevas tablas
-- ============================================
DESCRIBE eventos_mantenimiento;
DESCRIBE ordenes_mantenimiento;
DESCRIBE umbrales_alerta;
