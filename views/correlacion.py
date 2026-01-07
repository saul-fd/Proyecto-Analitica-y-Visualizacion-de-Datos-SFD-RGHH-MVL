import streamlit as st
import plotly.express as px
import pandas as pd
from utils import cargar_datos

st.set_page_config(page_title="Correlación de Pearson", layout="wide")

st.title("🔗 Análisis de Correlación (Pearson)")
st.markdown("""
Este módulo analiza la relación lineal entre las diferentes líneas del Metrobús.
* **Correlación cercana a 1:** Ambas líneas suben o bajan juntas.
* **Correlación cercana a 0:** No hay relación aparente.
""")

df = cargar_datos()

if df is not None:
    # 1. PREPARACIÓN DE DATOS (Pivotear)
    # Necesitamos una tabla donde cada columna sea una Línea y cada fila una Fecha
    df_pivot = df.pivot_table(index="fecha", columns="linea", values="afluencia", aggfunc="sum")
    
    # Limpiamos nulos si existen (días donde una línea no operó)
    df_pivot = df_pivot.fillna(0)

    # 2. CÁLCULO DE CORRELACIÓN DE PEARSON
    # El método .corr() de Pandas usa Pearson por defecto
    corr_matrix = df_pivot.corr(method='pearson')

    # --- VISUALIZACIÓN 1: MATRIZ DE CALOR ---
    st.subheader("1. Matriz de Correlación Global")
    fig_heat = px.imshow(
        corr_matrix,
        text_auto=".2f", # Muestra el valor con 2 decimales
        aspect="auto",
        color_continuous_scale="RdBu_r", # Rojo a Azul (Rojo=Positivo fuerte)
        origin="lower"
    )
    st.plotly_chart(fig_heat, use_container_width=True)

    st.divider()

    # --- VISUALIZACIÓN 2: ANÁLISIS DETALLADO (SCATTER PLOT) ---
    st.subheader("2. Comparativa Directa entre Líneas")
    
    col1, col2 = st.columns(2)
    with col1:
        eje_x = st.selectbox("Selecciona Línea X (Eje Horizontal)", df_pivot.columns, index=0)
    with col2:
        eje_y = st.selectbox("Selecciona Línea Y (Eje Vertical)", df_pivot.columns, index=1)

    # Gráfico de Dispersión con Línea de Tendencia (OLS)
    # OLS = Ordinary Least Squares (Regresión Lineal Simple) para ver la tendencia
    fig_scatter = px.scatter(
        df_pivot, 
        x=eje_x, 
        y=eje_y, 
        trendline="ols", 
        title=f"Correlación: {eje_x} vs {eje_y}",
        opacity=0.6
    )
    
    # Personalizar la línea de tendencia para que resalte
    fig_scatter.update_traces(marker=dict(size=5, color="#2980b9"), line=dict(color="red"))
    
    st.plotly_chart(fig_scatter, use_container_width=True)
    
    # Mostrar el valor R-Cuadrado o Correlación específica
    correlacion_par = df_pivot[eje_x].corr(df_pivot[eje_y])
    st.info(f"El Coeficiente de Pearson entre **{eje_x}** y **{eje_y}** es: **{correlacion_par:.4f}**")

else:
    st.error("No se pudieron cargar los datos.")
