import streamlit as st
import plotly.express as px
import numpy as np
from scipy.fft import fft, fftfreq
from utils import cargar_datos

st.set_page_config(page_title="Análisis Temporal", layout="wide")

st.title("⏳ Análisis Temporal y Espectral")
st.markdown("Detección de patrones cíclicos y evolución histórica.")

df = cargar_datos()

# --- SECCIÓN 1: TENDENCIA ---
st.subheader("1. Evolución Histórica")
# Agrupar por fecha para ver el total del sistema
df_diario = df.groupby("fecha")["afluencia"].sum().reset_index()

fig_main = px.line(df_diario, x="fecha", y="afluencia", title="Tendencia Diaria de Afluencia (Todo el Sistema)")
fig_main.update_traces(line_color="#2980b9")
st.plotly_chart(fig_main, use_container_width=True)

# --- SECCIÓN 2: MAPA DE CALOR (HEATMAP) ---
st.subheader("2. Intensidad por Mes y Línea")
# Tabla pivote para el mapa de calor
if 'mes' in df.columns:
    heatmap_data = df.groupby(['linea', 'mes'])['afluencia'].mean().reset_index()
    # Ordenar meses si es necesario, o usar pivot directamente
    try:
        matriz = df.pivot_table(index="linea", columns="mes", values="afluencia", aggfunc="mean").fillna(0)
        # Ordenar columnas de meses si es posible (opcional)
        fig_heat = px.imshow(matriz, color_continuous_scale="Viridis", aspect="auto")
        st.plotly_chart(fig_heat, use_container_width=True)
    except Exception as e:
        st.info("No se pudo generar el heatmap con los datos actuales.")

# --- SECCIÓN 3: FOURIER (ANÁLISIS ESPECTRAL) ---
st.divider()
st.subheader("3. Análisis Espectral (Transformada de Fourier)")
st.info("Este análisis descompone la serie de tiempo para encontrar ciclos repetitivos (ej. cada 7 días).")

col_fft_1, col_fft_2 = st.columns([3, 1])

with col_fft_1:
    # Preparar señal (usamos la afluencia diaria total)
    senal = df_diario["afluencia"].values
    n = len(senal)
    
    if n > 0:
        # Aplicar FFT
        yf = fft(senal)
        xf = fftfreq(n, d=1)[:n//2] # d=1 indica muestreo diario
        magnitud = 2.0/n * np.abs(yf[0:n//2])
        
        # Ignorar la frecuencia 0 (componente continua/promedio)
        mask = xf > 0.01 
        xf_plot = xf[mask]
        mag_plot = magnitud[mask]
        
        # Graficar Espectrograma
        fig_fft = px.bar(x=xf_plot, y=mag_plot, labels={'x': 'Frecuencia (1/días)', 'y': 'Potencia del Ciclo'})
        fig_fft.update_layout(title="Espectrograma de Frecuencias", xaxis_range=[0, 0.5])
        
        # Detectar pico máximo (Ciclo Dominante)
        idx_max = np.argmax(mag_plot)
        freq_max = xf_plot[idx_max]
        periodo_dias = 1 / freq_max
        
        fig_fft.add_annotation(
            x=freq_max, y=mag_plot[idx_max],
            text=f"Ciclo Principal: {periodo_dias:.1f} días",
            showarrow=True, arrowhead=2, ax=0, ay=-40
        )
        
        st.plotly_chart(fig_fft, use_container_width=True)

with col_fft_2:
    st.markdown("#### Interpretación")
    st.write(f"""
    El pico más alto ocurre en una frecuencia de **{freq_max:.3f}**.
    
    Esto equivale a un periodo de **{periodo_dias:.1f} días**.
    
    * **~7.0 días:** Indica un patrón semanal fuerte (Lunes-Viernes vs Fin de semana).
    * **~3.5 días:** Indica patrones de mitad de semana.
    """)
