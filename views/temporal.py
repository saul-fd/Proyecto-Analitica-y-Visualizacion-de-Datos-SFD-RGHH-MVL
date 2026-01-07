import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from scipy.fft import fft, fftfreq
from utils import cargar_datos

def show_temporal():
    # Estilos CSS (Sin bordes de colores tipo barra)
    st.markdown("""
    <style>
        .metric-box {
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            margin-top: 10px;
            border: 1px solid #e0e0e0;
        }
    </style>
    """, unsafe_allow_html=True)

    st.title("Analisis Espectral (Transformada de Fourier)")
    st.markdown("""
    Este modulo descompone la serie de tiempo para encontrar **patrones repetitivos**.
    """)

    try:
        df = cargar_datos()
    except Exception as e:
        st.error(f"Error cargando datos: {e}")
        return

    # --- FILTROS ---
    st.sidebar.header("Configuracion de Señal")
    opciones = ["Sistema Total"] + sorted(df["linea"].unique().tolist())
    seleccion = st.sidebar.selectbox("Seleccionar Serie a Analizar", opciones)

    # Preparar datos
    if seleccion == "Sistema Total":
        df_serie = df.groupby("fecha")["afluencia"].sum().reset_index()
    else:
        df_serie = df[df["linea"] == seleccion].groupby("fecha")["afluencia"].sum().reset_index()

    # Asegurar frecuencia diaria
    df_serie = df_serie.set_index("fecha").asfreq("D").fillna(method="ffill").reset_index()

    # --- 1. SEÑAL ORIGINAL ---
    st.subheader(f"1. Señal en el Tiempo: {seleccion}")
    fig_time = px.line(df_serie, x="fecha", y="afluencia", title="Serie Temporal Original")
    st.plotly_chart(fig_time, use_container_width=True)

    st.divider()

    # --- 2. GRAFICA DE AMPLITUD ESPECTRAL ---
    st.subheader("Grafica de Amplitud Espectral")
    
    y = df_serie["afluencia"].values
    n = len(y)
    y_detrend = y - np.mean(y)
    yf = fft(y_detrend)
    xf = fftfreq(n, 1)
    
    xf = xf[:n//2]
    magnitud = 2.0/n * np.abs(yf[0:n//2])
    
    df_fft = pd.DataFrame({"Frecuencia": xf, "Potencia": magnitud})
    df_fft["Periodo (Dias)"] = df_fft["Frecuencia"].apply(lambda x: 1/x if x > 0 else 0)
    
    # Filtro de ruido
    df_fft = df_fft[(df_fft["Frecuencia"] > 0.005) & (df_fft["Potencia"] > 100)]

    # Gráfica (ZOOM A 10 DÍAS)
    fig_fft = px.bar(
        df_fft, 
        x="Periodo (Dias)", 
        y="Potencia", 
        title="Amplitud Espectral (Zoom: 0-10 Dias)",
        labels={"Potencia": "Amplitud", "Periodo (Dias)": "Periodo del Ciclo (Dias)"}
    )
    # AQUI ESTA EL ZOOM SOLICITADO
    fig_fft.update_layout(xaxis_range=[0, 10]) 
    st.plotly_chart(fig_fft, use_container_width=True)

    # --- 3. RESULTADOS E INTERPRETACION ---
    if not df_fft.empty:
        idx_max = df_fft["Potencia"].idxmax()
        ciclo_top = df_fft.loc[idx_max, "Periodo (Dias)"]
        
        # Tarjeta del dato principal
        st.markdown('<div class="metric-box">', unsafe_allow_html=True)
        st.metric("Ciclo Principal Detectado", f"Cada {ciclo_top:.1f} Dias")
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown("###")
        
        # RECUADRO DE SIGNIFICADO DE CICLOS
        st.info("""        
        * **3.5 dias:** Patrones entre semana (pico los viernes y caida los lunes).
        * **7.0 dias:** Ciclo Semanal (Diferencia marcada entre dias laborales y fin de semana).
        * **15.0 dias:** Efecto Quincena (Pagos de nomina).
        * **30.0 dias:** Efecto Mensual (Cierre de mes).
        """)

    else:
        st.warning("No se encontraron ciclos claros con suficiente potencia.")
