# Documentación de Endpoints API

## Sistema de Control de Calidad Láser

Base URL: `http://localhost:8000`

---

## 📋 ÍNDICE

1. [Health Check](#health-check)
2. [Inspecciones](#inspecciones)
3. [Clasificación de Defectos](#clasificación-de-defectos)
4. [Lotes](#lotes)
5. [Alertas de Calidad](#alertas-de-calidad)
6. [Historial de Calidad por Cliente](#historial-de-calidad-por-cliente)
7. [Mantenimiento Preventivo](#mantenimiento-preventivo)

---

## 🏥 Health Check

### GET `/`
Verifica que el servidor está funcionando.

**Respuesta:**
```json
{
  "status": "online",
  "servicio": "Sistema de Control de Calidad Láser",
  "version": "2.0"
}
```

---

## 🔍 INSPECCIONES

### POST `/api/inspeccionar`
Inspecciona una imagen y determina si está APROBADA o RECHAZADA.

**Parámetros:**
- `file` (FormData): Archivo de imagen

**Respuesta:**
```json
{
  "status": "APROBADA" | "RECHAZADA",
  "max_distancia": 0.5,
  "puntos_defectuosos": [...],
  "alerta_info": {...}
}
```

---

### GET `/api/registros`
Lista todas las inspecciones guardadas.

**Respuesta:**
```json
{
  "inspecciones": [
    {
      "id": 1,
      "resultado": "APROBADA",
      "max_distancia": 0.5,
      "puntos_defectuosos": [...],
      "categoria": "Excluido",
      "fecha": "2025-12-14T10:30:00"
    }
  ]
}
```

---

### GET `/api/defectos`
Filtra inspecciones por categoría.

**Query Parameters:**
- `categoria` (opcional): Categoría de defecto

**Ejemplo:** `GET /api/defectos?categoria=Corte%20incompleto`

**Respuesta:**
```json
{
  "inspecciones": [...],
  "total": 10
}
```

---

### GET `/api/estadisticas/categorias`
Obtiene estadísticas agrupadas por categoría.

**Respuesta:**
```json
{
  "estadisticas": {
    "Corte incompleto": 5,
    "Rebaba severa": 3
  }
}
```

---

### GET `/api/inspecciones/completas`
Obtiene todas las inspecciones con información completa.

**Respuesta:**
```json
{
  "total": 100,
  "inspecciones": [...]
}
```

---

### DELETE `/api/inspecciones/{id}`
Elimina una inspección por ID.

**Respuesta:**
```json
{
  "mensaje": "Inspección eliminada correctamente"
}
```

---

### GET `/api/exportar`
Exporta todas las inspecciones a CSV.

**Respuesta:** Archivo CSV descargable

---

## 🏷️ CLASIFICACIÓN DE DEFECTOS

### POST `/api/clasificar-defecto`
Clasifica un defecto manualmente usando el sistema experto.

**Body:**
```json
{
  "descripcion": "Corte incompleto en borde superior",
  "color_borde": "Negro",
  "caracteristica_borde": "Irregular",
  "profundidad_corte": 2.5,
  "espesor_material": 1.0,
  "dimension_fuera_rango": false,
  "falla_maquina": true,
  "desalineado": false,
  "deformacion_material": false
}
```

**Respuesta:**
```json
{
  "id": 1,
  "categoria": "Corte incompleto",
  "fecha": "2025-12-14T10:30:00"
}
```

---

## 📦 LOTES

### POST `/api/lotes`
Crea un nuevo lote.

**Body:**
```json
{
  "codigo_lote": "LOTE-001",
  "inspector": "Juan Pérez",
  "cliente": "Cliente ABC",
  "tipo_producto": "Producto X",
  "orden": "ORD-123"
}
```

**Respuesta:**
```json
{
  "id": 1,
  "codigo_lote": "LOTE-001",
  "inspector": "Juan Pérez",
  "estado": "EN PROCESO",
  "fecha": "2025-12-14T10:30:00",
  "cliente": "Cliente ABC",
  "tipo_producto": "Producto X",
  "orden": "ORD-123"
}
```

---

### GET `/api/lotes/listar`
Lista todos los lotes.

**Respuesta:**
```json
{
  "lotes": [
    {
      "id": 1,
      "codigo_lote": "LOTE-001",
      "inspector": "Juan Pérez",
      "estado": "EN PROCESO",
      "fecha": "2025-12-14T10:30:00",
      "total_inspecciones": 5
    }
  ]
}
```

---

### GET `/api/lotes/{id_lote}`
Obtiene un lote específico con sus inspecciones.

**Respuesta:**
```json
{
  "id": 1,
  "codigo_lote": "LOTE-001",
  "inspector": "Juan Pérez",
  "estado": "EN PROCESO",
  "fecha": "2025-12-14T10:30:00",
  "inspecciones": [...]
}
```

---

### POST `/api/lotes/{id_lote}/agregar-inspeccion`
Agrega una inspección a un lote.

**Body:**
```json
{
  "id_inspeccion": 5
}
```

**Respuesta:**
```json
{
  "mensaje": "Inspección agregada al lote correctamente",
  "inspeccion_id": 5,
  "lote_id": 1
}
```

---

### GET `/api/lotes/{id_lote}/exportar`
Exporta todas las inspecciones de un lote a CSV.

**Respuesta:** Archivo CSV descargable

---

## 🚨 ALERTAS DE CALIDAD

### GET `/api/alertas/estadisticas`
Obtiene estadísticas actuales de calidad.

**Respuesta:**
```json
{
  "porcentaje_defectos": 5.5,
  "total_inspecciones": 100,
  "total_rechazados": 5,
  "total_aprobados": 95
}
```

---

### GET `/api/alertas/historial`
Obtiene el historial de alertas.

**Query Parameters:**
- `limite` (opcional, default: 50): Número máximo de alertas

**Respuesta:**
```json
{
  "alertas": [
    {
      "id": 1,
      "tipo_alerta": "Umbral superado",
      "porcentaje_defectos": 5.5,
      "fecha": "2025-12-14T10:30:00"
    }
  ]
}
```

---

### POST `/api/alertas/verificar`
Verifica manualmente si se debe crear una alerta.

**Respuesta:**
```json
{
  "alerta_creada": true,
  "alerta_id": 1,
  "estadisticas": {...}
}
```

---

### POST `/api/alertas/test-email`
Envía un email de prueba.

**Respuesta:**
```json
{
  "success": true,
  "mensaje": "Email de prueba enviado correctamente"
}
```

---

## 📊 HISTORIAL DE CALIDAD POR CLIENTE

### GET `/api/historial-calidad`
Consulta el historial de calidad con filtros y paginación.

**Query Parameters:**
- `cliente` (opcional): Nombre del cliente
- `fecha_inicio` (opcional): Fecha inicio (YYYY-MM-DD)
- `fecha_fin` (opcional): Fecha fin (YYYY-MM-DD)
- `tipo_producto` (opcional): Tipo de producto
- `estado` (opcional): Estado del producto
- `pagina` (opcional, default: 1): Número de página
- `por_pagina` (opcional, default: 20): Registros por página
- `orden` (opcional, default: "desc"): "asc" o "desc"
- `usuario` (opcional): Usuario para auditoría

**Ejemplo:** `GET /api/historial-calidad?cliente=ABC&pagina=1&por_pagina=20`

**Respuesta:**
```json
{
  "registros": [
    {
      "id": 1,
      "estado": "RECHAZADA",
      "fecha_inspeccion": "2025-12-14T10:30:00",
      "responsable": "Juan Pérez",
      "lote": "LOTE-001",
      "orden": "ORD-123",
      "cliente": "Cliente ABC",
      "tipo_producto": "Producto X",
      "categoria": "Corte incompleto",
      "observaciones": "..."
    }
  ],
  "paginacion": {
    "pagina_actual": 1,
    "por_pagina": 20,
    "total_registros": 100,
    "total_paginas": 5,
    "tiene_siguiente": true,
    "tiene_anterior": false
  }
}
```

---

### GET `/api/historial-calidad/exportar-pdf`
Exporta el historial de calidad a PDF.

**Query Parameters:**
- `cliente` (opcional)
- `fecha_inicio` (opcional)
- `fecha_fin` (opcional)
- `tipo_producto` (opcional)
- `estado` (opcional)
- `usuario` (opcional)

**Respuesta:** Archivo PDF descargable

---

### GET `/api/historial-calidad/exportar-excel`
Exporta el historial de calidad a Excel.

**Query Parameters:** (mismos que PDF)

**Respuesta:** Archivo Excel descargable

---

## 🔧 MANTENIMIENTO PREVENTIVO

### POST `/api/mantenimiento/registrar-evento`
Registra un evento de mantenimiento y verifica si debe crear una orden preventiva.

**Body:**
```json
{
  "maquina": "MAQUINA_01",
  "tipo_evento": "Rebaba severa",
  "inspeccion_id": 5,
  "lote_id": 1,
  "turno": "TURNO_1",
  "responsable": "Juan Pérez"
}
```

**Respuesta:**
```json
{
  "evento_id": 1,
  "orden_info": {
    "orden_creada": true,
    "orden_id": 1,
    "prioridad": "MEDIA",
    "eventos_asociados": 3,
    "mensaje": "Orden preventiva creada por 3 eventos en 60 minutos"
  }
}
```

---

### GET `/api/mantenimiento/alertas`
Obtiene todas las alertas/órdenes de mantenimiento activas.

**Query Parameters:**
- `maquina` (opcional): Filtrar por máquina

**Respuesta:**
```json
{
  "alertas": [
    {
      "id": 1,
      "maquina": "MAQUINA_01",
      "tipo_patron": "Rebaba severa",
      "prioridad": "ALTA",
      "estado": "ABIERTA",
      "ventana_sugerida": "2025-12-15T10:30:00",
      "responsable": "Juan Pérez",
      "fecha_creacion": "2025-12-14T10:30:00",
      "eventos_asociados": 3,
      "creado_por": "Sistema"
    }
  ],
  "total": 1
}
```

---

### GET `/api/mantenimiento/historial`
Obtiene el historial de eventos y órdenes de mantenimiento.

**Query Parameters:**
- `maquina` (opcional): Filtrar por máquina
- `fecha_inicio` (opcional): Fecha inicio (YYYY-MM-DD)
- `fecha_fin` (opcional): Fecha fin (YYYY-MM-DD)
- `estado` (opcional): Estado del evento
- `tipo_evento` (opcional): Tipo de evento

**Respuesta:**
```json
{
  "historial": [
    {
      "id": 1,
      "maquina": "MAQUINA_01",
      "tipo_evento": "Rebaba severa",
      "fecha_hora": "2025-12-14T10:30:00",
      "lote": "LOTE-001",
      "turno": "TURNO_1",
      "responsable": "Juan Pérez",
      "estado": "ABIERTA",
      "orden_mantenimiento_id": 1
    }
  ],
  "total": 1
}
```

---

### POST `/api/mantenimiento/ordenes/{orden_id}/marcar-realizada`
Marca una orden de mantenimiento como realizada.

**Body:**
```json
{
  "accion_correctiva": "Se realizó limpieza y calibración de la máquina",
  "evidencia": "Fotos y reporte adjuntos",
  "usuario": "Juan Pérez"
}
```

**Respuesta:**
```json
{
  "success": true,
  "mensaje": "Orden marcada como realizada",
  "orden_id": 1,
  "eventos_actualizados": 3
}
```

---

### POST `/api/mantenimiento/ordenes/{orden_id}/asignar-responsable`
Asigna un responsable a una orden de mantenimiento.

**Body:**
```json
{
  "responsable": "Juan Pérez",
  "usuario": "admin"
}
```

**Respuesta:**
```json
{
  "success": true,
  "mensaje": "Responsable asignado",
  "orden_id": 1
}
```

---

### GET `/api/mantenimiento/plan/exportar-pdf`
Exporta el plan de mantenimiento preventivo a PDF.

**Query Parameters:**
- `maquina` (opcional): Filtrar por máquina
- `usuario` (opcional): Usuario que exporta

**Respuesta:** Archivo PDF descargable

---

### GET `/api/mantenimiento/plan/exportar-excel`
Exporta el plan de mantenimiento preventivo a Excel.

**Query Parameters:** (mismos que PDF)

**Respuesta:** Archivo Excel descargable

---

### POST `/api/mantenimiento/umbrales`
Configura o actualiza un umbral de alerta.

**Body:**
```json
{
  "maquina": "MAQUINA_01",
  "tipo_defecto": "Rebaba severa",
  "umbral_eventos": 3,
  "ventana_tiempo_minutos": 60,
  "umbral_porcentaje_lote": 5.0,
  "activo": true
}
```

**Respuesta:**
```json
{
  "success": true,
  "mensaje": "Umbral creado correctamente",
  "umbral_id": 1
}
```

---

### GET `/api/mantenimiento/umbrales`
Lista los umbrales de alerta configurados.

**Query Parameters:**
- `maquina` (opcional): Filtrar por máquina
- `activo` (opcional): Filtrar por estado activo (true/false)

**Respuesta:**
```json
{
  "umbrales": [
    {
      "id": 1,
      "maquina": "MAQUINA_01",
      "tipo_defecto": "Rebaba severa",
      "umbral_eventos": 3,
      "ventana_tiempo_minutos": 60,
      "umbral_porcentaje_lote": 5.0,
      "activo": true,
      "fecha_creacion": "2025-12-14T10:30:00"
    }
  ],
  "total": 1
}
```

---

## 📝 NOTAS

- Todos los endpoints que requieren autenticación deberían incluir el header `Authorization` (pendiente de implementar)
- Los formatos de fecha son ISO 8601: `YYYY-MM-DD` o `YYYY-MM-DDTHH:MM:SS`
- Los archivos de exportación (CSV, PDF, Excel) se descargan directamente
- Los endpoints de mantenimiento se integran automáticamente con el sistema de inspecciones

---

## 🔗 Documentación Interactiva

Una vez que el servidor esté corriendo, puedes acceder a:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

