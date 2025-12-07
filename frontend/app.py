import streamlit as st
import requests
import pandas as pd

API_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="Control de Calidad Láser", layout="wide")

# ============================
# MENÚ SUPERIOR (SENCILLO Y ELEGANTE)
# ============================

st.title("🏭 Sistema de Control de Calidad Láser")

menu = st.radio(
    "Navegación",
    ["🏠 Inicio", "🔍 Inspeccionar", "📜 Registros", "📦 Lotes", "🚨 Alertas", "📊 Estadísticas", "📅 Reportes", "📤 Exportar"],
    horizontal=True
)

st.markdown("---")

# ============================
# 🏠 INICIO
# ============================

if menu == "🏠 Inicio":
    st.header("Bienvenido al Sistema Automatizado de Inspección Láser")

    col1, col2 = st.columns(2)

    with col1:
        st.image("assets/banner.png", caption="Máquina de corte láser", use_column_width=True)

    with col2:
        st.subheader("Sobre el sistema")
        st.write("""
        Este sistema permite:
        - 🔍 Analizar imágenes para detectar rebaba o defectos
        - 📦 Gestionar lotes de inspecciones
        - 📜 Registrar automáticamente cada análisis
        - 🚨 Enviar alertas automáticas por correo
        - 📊 Mostrar estadísticas para supervisión
        """)

    st.success("Usa el menú superior para navegar entre módulos.")

# ============================
# 🔍 INSPECCIONAR IMAGEN
# ============================

elif menu == "🔍 Inspeccionar":
    st.header("Análisis automático de imagen")

    uploaded_file = st.file_uploader("Selecciona una imagen", type=["png", "jpg", "jpeg"])

    if uploaded_file:
        st.image(uploaded_file, width=350)

        if st.button("Procesar imagen"):
            files = {"file": (uploaded_file.name, uploaded_file, uploaded_file.type)}
            resp = requests.post(f"{API_URL}/api/inspeccionar", files=files)

            if resp.status_code == 200:
                st.success("Procesado correctamente")
                st.json(resp.json())
            else:
                st.error("Error al procesar imagen")

# ============================
# 📜 REGISTROS
# ============================

elif menu == "📜 Registros":
    st.header("Historial de inspecciones")

    if st.button("Cargar registros"):
        resp = requests.get(f"{API_URL}/api/registros")

        if resp.status_code == 200:
            registros = resp.json().get("inspecciones", [])
            if len(registros) == 0:
                st.info("No hay registros todavía")
            else:
                st.dataframe(pd.DataFrame(registros), use_container_width=True)
        else:
            st.error("Error al obtener registros")

# ============================
# 📦 LOTES
# ============================

elif menu == "📦 Lotes":
    st.header("Gestión de Lotes")

    st.subheader("Crear nuevo lote")
    codigo = st.text_input("Código del lote")
    inspector = st.text_input("Inspector")

    if st.button("Crear lote"):
        resp = requests.post(f"{API_URL}/api/lotes", json={
            "codigo_lote": codigo,
            "inspector": inspector
        })
        st.json(resp.json())

    st.markdown("---")

    st.subheader("Listar lotes")
    if st.button("Cargar lotes"):
        resp = requests.get(f"{API_URL}/api/lotes")
        st.dataframe(pd.DataFrame(resp.json().get("lotes", [])))

# ============================
# 🚨 ALERTAS
# ============================

elif menu == "🚨 Alertas":
    st.header("Sistema de Alertas")

    if st.button("Verificar alertas"):
        resp = requests.get(f"{API_URL}/api/alertas/verificar")
        st.json(resp.json())

    st.markdown("---")

    if st.button("Enviar email de prueba"):
        resp = requests.get(f"{API_URL}/api/alertas/test-email")
        st.json(resp.json())

# ============================
# 📊 ESTADÍSTICAS
# ============================

elif menu == "📊 Estadísticas":
    st.header("Estadísticas por categoría")

    resp = requests.get(f"{API_URL}/api/estadisticas/categorias")

    if resp.status_code == 200:
        data = resp.json()["estadisticas"]
        df = pd.DataFrame(list(data.items()), columns=["Categoría", "Cantidad"])
        st.bar_chart(df, x="Categoría", y="Cantidad")
    else:
        st.error("No se pudieron cargar estadísticas")

# ============================
# 📅 REPORTES SEMANALES
# ============================

elif menu == "📅 Reportes":
    st.header("📅 Reporte Semanal de Calidad")
    st.write("Genera, visualiza y descarga el reporte semanal de calidad.")

    st.subheader("Seleccionar rango de fechas")

    fecha_inicio = st.date_input("Fecha inicio")
    fecha_fin = st.date_input("Fecha fin")

    st.markdown("---")

    # ============================
    # 📊 GENERAR REPORTE (JSON)
    # ============================
    if st.button("📊 Generar reporte semanal"):
        if fecha_inicio > fecha_fin:
            st.error("La fecha inicio no puede ser mayor que la fecha fin.")
        else:
            url = f"{API_URL}/api/reportes/semanal"
            params = {
                "fecha_inicio": fecha_inicio.isoformat(),
                "fecha_fin": fecha_fin.isoformat()
            }

            with st.spinner("Generando reporte..."):
                resp = requests.get(url, params=params)

                if resp.status_code == 200:
                    datos = resp.json()

                    st.success("Reporte generado correctamente")
                    st.write("### Resumen")

                    st.json(datos)

                else:
                    st.error("Error al generar reporte")

    st.markdown("---")

    # ============================
    # 📥 DESCARGAR EXCEL
    # ============================
    if st.button("📥 Descargar Excel"):
        if fecha_inicio > fecha_fin:
            st.error("La fecha inicio no puede ser mayor que la fecha fin.")
        else:
            url = f"{API_URL}/api/reportes/semanal/excel"
            params = {
                "fecha_inicio": fecha_inicio.isoformat(),
                "fecha_fin": fecha_fin.isoformat()
            }

            with st.spinner("Descargando archivo Excel..."):
                resp = requests.get(url, params=params)

                if resp.status_code == 200:
                    st.download_button(
                        label="📥 Descargar archivo Excel",
                        data=resp.content,
                        file_name=f"reporte_semanal_{fecha_inicio}_{fecha_fin}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                else:
                    st.error("No se pudo generar el archivo")

    st.markdown("---")

    # ============================
    # 📧 ENVIAR REPORTE POR EMAIL (OPCIONAL)
    # ============================
    if st.button("📧 Enviar reporte semanal por email"):
        resp = requests.post(f"{API_URL}/api/alertas/programar-reporte")

        if resp.status_code == 200:
            st.success("Reporte enviado por correo correctamente.")
        else:
            st.error("Error al enviar correo.")

