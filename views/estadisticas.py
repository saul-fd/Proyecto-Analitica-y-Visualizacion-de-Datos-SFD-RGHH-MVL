import streamlit as st
import plotly.express as px
import pandas as pd
from utils import cargar_datos

def show_estadisticas():
    # --- ESTILOS CSS ---
    st.markdown("""
    <style>
        .stMetric { background-color: #f0f2f6; padding: 10px; border-radius: 5px; }
        /* Ajuste para tablas */
        .dataframe { font-size: 12px; }
    </style>
    """, unsafe_allow_html=True)

    st.title("📊 Distribución y Estadística Descriptiva")
    st.markdown("Análisis profundo de la dispersión, tendencia central y forma de los datos.")

    try:
        df = cargar_datos()
    except Exception as e:
        st.error(f"Error cargando datos: {e}")
        return

    # --- SECCIÓN 1: HISTOGRAMAS (DISTRIBUCIÓN) ---
    st.subheader("1. Forma de la Distribución (Histograma)")
    st.markdown("""
    ¿Los datos siguen una campana de Gauss (Normal)? 
    * **Simétrica:** La mayoría de días tienen una afluencia media.
    * **Sesgada:** Hay muchos días de baja afluencia o picos extremos.
    """)
    
    # Filtro local para esta gráfica
    opciones_linea = ["Todas"] + sorted(df["linea"].unique().tolist())
    linea_sel = st.selectbox("Filtrar Histograma por Línea", opciones_linea)
    
    df_plot = df if linea_sel == "Todas" else df[df["linea"] == linea_sel]
    
    # Histograma con Boxplot marginal superior
    fig_hist = px.histogram(
        df_plot, 
        x="afluencia", 
        nbins=50, 
        marginal="box", # Agrega un boxplot pequeño arriba
        title=f"Distribución de Frecuencias - {linea_sel}",
        color_discrete_sequence=["#27ae60"],
        opacity=0.7
    )
    fig_hist.update_layout(template="plotly_white", xaxis_title="Afluencia de Pasajeros", yaxis_title="Frecuencia (Días)")
    st.plotly_chart(fig_hist, use_container_width=True)

    st.divider()

    # --- SECCIÓN 2: COMPARATIVA DE VARIABILIDAD ---
    st.subheader("2. Comparativa Global (Boxplots)")
    st.markdown("Comparación directa de rangos y valores atípicos entre todas las líneas.")
    
    # Ordenamos por mediana para que se vea escalonado y bonito
    medianas = df.groupby("linea")["afluencia"].median().sort_values(ascending=False).index
    
    fig_box = px.box(
        df, 
        x="linea", 
        y="afluencia", 
        color="linea",
        category_orders={"linea": medianas}, # Ordenar por volumen
        title="Dispersión de Afluencia por Línea (Ordenado por Mediana)"
    )
    fig_box.update_layout(template="plotly_white", showlegend=False)
    st.plotly_chart(fig_box, use_container_width=True)

    # --- SECCIÓN 3: TABLA DE ESTADÍSTICOS ---
    st.subheader("3. Resumen Estadístico Detallado")
    
    # Agrupamos y calculamos métricas clave
    resumen = df.groupby("linea")["afluencia"].describe().reset_index()
    
    # Añadimos la Varianza (cuadrado de la desviación estándar)
    resumen["varianza"] = resumen["std"] ** 2
    
    # Reordenar columnas para mejor lectura
    cols = ["linea", "count", "mean", "std", "min", "25%", "50%", "75%", "max"]
    resumen = resumen[cols]
    
    st.markdown("Tabla interactiva con métricas clave (Media, Desviación Estándar, Cuartiles):")
    
    # Formateamos para que se vea profesional (sin decimales excesivos)
    st.dataframe(
        resumen.style.format({
            "count": "{:,.0f}",
            "mean": "{:,.0f}", 
            "std": "{:,.0f}", 
            "min": "{:,.0f}", 
            "25%": "{:,.0f}", 
            "50%": "{:,.0f}", 
            "75%": "{:,.0f}", 
            "max": "{:,.0f}"
        }).background_gradient(subset=["mean"], cmap="Blues"), # Colorear la media
        use_container_width=True
    )
