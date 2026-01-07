import streamlit as st
import plotly.express as px
import pandas as pd
from utils import cargar_datos

st.set_page_config(page_title="Estadística Descriptiva", layout="wide")

st.title("📊 Distribución y Estadística Descriptiva")
st.markdown("Análisis de la dispersión, tendencia central y forma de los datos.")

df = cargar_datos()

if df is not None:
    # --- SECCIÓN 1: HISTOGRAMAS (DISTRIBUCIÓN) ---
    st.subheader("1. Histograma de Afluencia")
    st.markdown("Permite observar la frecuencia de los volúmenes de pasajeros. ¿Es una distribución Normal?")
    
    linea_sel = st.selectbox("Filtrar por Línea (Opcional)", ["Todas"] + sorted(df["linea"].unique().tolist()))
    
    df_plot = df if linea_sel == "Todas" else df[df["linea"] == linea_sel]
    
    # Histograma con Boxplot marginal arriba
    fig_hist = px.histogram(
        df_plot, 
        x="afluencia", 
        nbins=50, 
        marginal="box", # Agrega un boxplot pequeño arriba
        title=f"Distribución de Frecuencias - {linea_sel}",
        color_discrete_sequence=["#27ae60"]
    )
    st.plotly_chart(fig_hist, use_container_width=True)

    st.divider()

    # --- SECCIÓN 2: COMPARATIVA DE DISPERSIÓN (BOXPLOTS) ---
    st.subheader("2. Comparativa de Variabilidad (Boxplots)")
    st.markdown("Los puntos fuera de los 'bigotes' se consideran valores atípicos (outliers).")
    
    fig_box = px.box(
        df, 
        x="linea", 
        y="afluencia", 
        color="linea",
        title="Dispersión de Afluencia por Línea"
    )
    st.plotly_chart(fig_box, use_container_width=True)

    # --- SECCIÓN 3: TABLA DE ESTADÍSTICOS ---
    st.subheader("3. Resumen Estadístico")
    
    # Agrupamos y calculamos métricas clave
    resumen = df.groupby("linea")["afluencia"].describe().reset_index()
    
    # Formateamos para que se vea bonito
    st.dataframe(
        resumen.style.format({
            "mean": "{:,.0f}", 
            "std": "{:,.0f}", 
            "min": "{:,.0f}", 
            "25%": "{:,.0f}", 
            "50%": "{:,.0f}", 
            "75%": "{:,.0f}", 
            "max": "{:,.0f}"
        }),
        use_container_width=True
    )

else:
    st.error("No se pudieron cargar los datos.")
