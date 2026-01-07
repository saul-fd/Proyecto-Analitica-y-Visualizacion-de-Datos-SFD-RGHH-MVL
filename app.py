import streamlit as st
import pandas as pd
import plotly.express as px
import os
from utils import cargar_datos

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Tablero Metrobús CDMX",
    page_icon="🚌",
    layout="wide"
)

# --- CONFIGURACIÓN VISUAL ---
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

st.markdown("""
<style>
    /* Estilo para las métricas superiores */
    .metric-container {
        background-color: white;
        padding: 10px;
        border-radius: 8px;
        border-top: 5px solid #ccc;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .metric-value {
        font-size: 18px;
        font-weight: bold;
        color: #2c3e50;
    }
    .metric-label {
        font-size: 12px;
        color: #7f8c8d;
        margin-top: 4px;
    }
</style>
""", unsafe_allow_html=True)

# --- FUNCIÓN: GENERAR KPI POR LÍNEA ---
def mostrar_resumen_lineas(df):
    # 1. Cálculo del Promedio General (Sistema)
    # Agrupamos por fecha primero para sumar todas las líneas por día
    diario_sistema = df.groupby("fecha")["afluencia"].sum()
    promedio_gral = diario_sistema.mean()
    
    # 2. Cálculo del Promedio por Línea
    # Agrupamos por línea y fecha, luego promediamos los días
    diario_linea = df.groupby(["linea", "fecha"])["afluencia"].sum().reset_index()
    promedios_linea = diario_linea.groupby("linea")["afluencia"].mean()
    
    # Lista de líneas ordenadas
    lineas = sorted(promedios_linea.index.tolist())
    
    # Desplegar columnas: 1 para General + N para líneas
    st.markdown("### 📊 Promedios Diarios de Afluencia")
    cols = st.columns(len(lineas) + 1)
    
    # A) Tarjeta General
    with cols[0]:
        st.markdown(f"""
        <div class="metric-container" style="border-top-color: #2c3e50;">
            <div style="font-size: 20px;">🚍</div>
            <div class="metric-value">{promedio_gral:,.0f}</div>
            <div class="metric-label">Sistema Total</div>
        </div>
        """, unsafe_allow_html=True)
        
    # B) Tarjetas por Línea
    for i, linea in enumerate(lineas):
        val = promedios_linea[linea]
        color = COLOR_MAP.get(linea, "#95a5a6")
        numero = linea.replace("Línea ", "L")
        
        with cols[i+1]:
            st.markdown(f"""
            <div class="metric-container" style="border-top-color: {color};">
                <div style="color: {color}; font-weight:bold;">{numero}</div>
                <div class="metric-value">{val:,.0f}</div>
                <div class="metric-label">Promedio Diario</div>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("---")

# --- CARGA DE DATOS ---
df = cargar_datos()

if df is not None:
    # 1. MOSTRAR ENCABEZADO CON PROMEDIOS (Reemplaza al carrusel de imágenes)
    mostrar_resumen_lineas(df)

    st.subheader("📈 Evolución Temporal y Distribución")

    # Preparar datos para las gráficas
    # Agrupación diaria por línea para la gráfica de tiempo
    df_chart = df.groupby(["fecha", "linea"])["afluencia"].sum().reset_index()
    
    # Asignar colores al DataFrame para que Plotly los use automáticamente
    color_discrete_map = COLOR_MAP

    # 2. DASHBOARD
    col1, col2 = st.columns([3, 1])

    with col1:
        st.markdown("**Evolución de Afluencia por Línea** (Histórico)")
        # Gráfica de Líneas (Soporta N elementos y muestra tiempo)
        fig_line = px.line(
            df_chart, 
            x="fecha", 
            y="afluencia", 
            color="linea",
            color_discrete_map=color_discrete_map,
            markers=False
        )
        fig_line.update_layout(
            template="plotly_white",
            xaxis_title="Fecha",
            yaxis_title="Usuarios Diarios",
            legend_title="",
            hovermode="x unified",
            height=450
        )
        st.plotly_chart(fig_line, use_container_width=True)

    with col2:
        st.markdown("**Distribución Total**")
        # Gráfica de Pastel (Soporta N elementos para ver proporción)
        df_pie = df.groupby("linea")["afluencia"].sum().reset_index()
        
        fig_pie = px.pie(
            df_pie, 
            values="afluencia", 
            names="linea",
            color="linea",
            color_discrete_map=color_discrete_map,
            hole=0.4
        )
        fig_pie.update_layout(
            template="plotly_white",
            showlegend=False,
            height=450,
            margin=dict(l=20, r=20, t=20, b=20)
        )
        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_pie, use_container_width=True)

else:
    st.error("No se pudieron cargar los datos. Verifica `utils.py` y la carpeta `data/`.")
