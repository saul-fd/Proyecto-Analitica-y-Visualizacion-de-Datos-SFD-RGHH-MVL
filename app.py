import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import os
from utils import cargar_datos  # Importamos tu función centralizada

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="MI Movilidad CDMX",
    page_icon="🚌",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# 🎨 CONFIGURACIÓN VISUAL (Colores e Imágenes)
# ==========================================
DICCIONARIO_IMAGENES = {
    "Línea 1": "MB-1.png",
    "Línea 2": "MB-2.png",
    "Línea 3": "MB-3.png",
    "Línea 4": "MB-4.png",
    "Línea 5": "MB-5.png",
    "Línea 6": "MB-6.png",
    "Línea 7": "MB-7.png",
    "Emergente": "ícono-MB.png"
}

COLOR_MAP = {
    'Línea 1': '#B71C1C', # Rojo
    'Línea 2': '#4A148C', # Morado
    'Línea 3': '#558B2F', # Verde Oliva
    'Línea 4': '#E65100', # Naranja
    'Línea 5': '#0277BD', # Azul
    'Línea 6': '#EC407A', # Rosa
    'Línea 7': '#2E7D32', # Verde
    'Emergente': '#616161' # Gris
}

# --- ESTILOS CSS ---
st.markdown("""
<style>
    .kpi-card {
        background-color: white;
        border-radius: 8px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        text-align: center;
        border-bottom: 4px solid #00b894;
        margin-bottom: 20px;
    }
    .kpi-value {
        font-size: 26px;
        font-weight: 800;
        color: #2d3436;
        margin: 5px 0;
    }
    .kpi-label {
        font-size: 13px;
        color: #636e72;
        text-transform: uppercase;
        font-weight: 600;
    }
    /* Estilo para fallback de iconos */
    .line-badge {
        width: 50px; height: 50px; border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        color: white; font-weight: bold; margin: 0 auto;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 🧩 COMPONENTES DE LA UI
# ==========================================
def mostrar_encabezado_lineas():
    st.markdown("###")
    cols = st.columns(len(DICCIONARIO_IMAGENES))
    for i, (nombre, archivo) in enumerate(DICCIONARIO_IMAGENES.items()):
        with cols[i]:
            ruta = os.path.join("imagenes", archivo)
            if os.path.exists(ruta):
                st.image(ruta, width=60)
            else:
                # Si no encuentra la imagen, dibuja un círculo con CSS
                color = COLOR_MAP.get(nombre, "#333")
                st.markdown(f'<div class="line-badge" style="background-color:{color};">{i+1}</div>', unsafe_allow_html=True)
                st.markdown(f"<div style='text-align:center; font-size:10px;'>{nombre}</div>", unsafe_allow_html=True)
    st.markdown("---")

def mostrar_kpi(col, titulo, valor, icono):
    col.markdown(f"""
        <div class="kpi-card">
            <div style="font-size:24px;">{icono}</div>
            <div class="kpi-value">{valor}</div>
            <div class="kpi-label">{titulo}</div>
        </div>
    """, unsafe_allow_html=True)

# ==========================================
# 🚀 EJECUCIÓN PRINCIPAL
# ==========================================
df = cargar_datos()

if df is not None:
    # Generar columnas de fecha adicionales para visualización
    if 'fecha' in df.columns:
        df['Mes'] = df['fecha'].dt.month_name() if hasattr(df['fecha'].dt, 'month_name') else df['fecha'].dt.month
        df['Mes_Num'] = df['fecha'].dt.month

    # 1. Header Visual
    mostrar_encabezado_lineas()
    st.title("Tablero General de Afluencia Metrobús")

    # 2. Sidebar de Filtro Global
    lista_lineas = ["Todas"] + sorted(df["linea"].unique().tolist())
    filtro_linea = st.sidebar.selectbox("📍 Filtrar Dashboard por Línea", lista_lineas)

    # Aplicar Filtro
    df_view = df.copy()
    if filtro_linea != "Todas":
        df_view = df_view[df_view["linea"] == filtro_linea]

    # 3. KPIs
    total = df_view["afluencia"].sum()
    promedio = df_view["afluencia"].mean()
    maximo = df_view["afluencia"].max()
    registros = len(df_view)

    c1, c2, c3, c4 = st.columns(4)
    mostrar_kpi(c1, "Viajes Totales", f"{total:,.0f}", "🚌")
    mostrar_kpi(c2, "Promedio Diario", f"{promedio:,.0f}", "📊")
    mostrar_kpi(c3, "Pico Máximo", f"{maximo:,.0f}", "🏆")
    mostrar_kpi(c4, "Días Analizados", f"{registros}", "📅")

    # 4. Gráficas Principales
    st.markdown("###") # Espaciador
    
    # Gráfica A: Barras por línea (solo si vemos todas)
    if filtro_linea == "Todas":
        st.subheader("Comparativa por Línea")
        df_lineas = df_view.groupby("linea")["afluencia"].sum().reset_index().sort_values("afluencia", ascending=True)
        colores = [COLOR_MAP.get(l, '#333') for l in df_lineas["linea"]]
        
        fig_bar = px.bar(df_lineas, x="afluencia", y="linea", orientation="h", text_auto='.3s')
        fig_bar.update_traces(marker_color=colores)
        fig_bar.update_layout(template="plotly_white", yaxis_title="", xaxis_title="Total Viajes")
        st.plotly_chart(fig_bar, use_container_width=True)

    # Gráfica B y C: Tiempo y Meses
    col_izq, col_der = st.columns([2, 1])
    
    with col_izq:
        st.subheader("Evolución Diaria")
        df_tiempo = df_view.groupby("fecha")["afluencia"].sum().reset_index()
        color_graf = COLOR_MAP.get(filtro_linea, "#2980b9") if filtro_linea != "Todas" else "#2980b9"
        
        fig_area = px.area(df_tiempo, x="fecha", y="afluencia")
        fig_area.update_traces(line_color=color_graf, fillcolor=color_graf)
        fig_area.update_layout(template="plotly_white", margin=dict(l=20, r=20, t=30, b=20))
        st.plotly_chart(fig_area, use_container_width=True)

    with col_der:
        st.subheader("Comportamiento Mensual")
        if 'Mes' in df_view.columns:
            df_mes = df_view.groupby(['Mes_Num', 'Mes'])["afluencia"].sum().reset_index().sort_values('Mes_Num')
            fig_mes = px.bar(df_mes, x='Mes', y='afluencia')
            fig_mes.update_traces(marker_color="#00b894")
            fig_mes.update_layout(template="plotly_white", margin=dict(l=20, r=20, t=30, b=20))
            st.plotly_chart(fig_mes, use_container_width=True)

else:
    st.error("Error al cargar los datos. Verifica tu archivo utils.py y la carpeta data/")
