import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from scipy.fft import fft, fftfreq
from utils import cargar_datos

def show_temporal():
    # Estilos CSS 
    st.markdown("""
    <style>
        .metric-box {
            background-color: #f8f9fa;
            border-left: 5px solid #2980b9;
            padding: 15px;
            border-radius: 5px;
            margin-top: 10px;
        }
    </style>
    """, unsafe_allow_html=True)

    st.title("Analisis Temporal")
    st.markdown("""
    Este modulo muestra la serie de tiempo para encontrar **patrones repetitivos**.
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

    # Preparar datos (Agrupar por día)
    if seleccion == "Sistema Total":
        df_serie = df.groupby("fecha")["afluencia"].sum().reset_index()
    else:
        df_serie = df[df["linea"] == seleccion].groupby("fecha")["afluencia"].sum().reset_index()

    # Asegurar frecuencia diaria (rellenar huecos)
    df_serie = df_serie.set_index("fecha").asfreq("D").fillna(method="ffill").reset_index()

    # --- 1. VISUALIZACIÓN DE LA SEÑAL ---
    st.subheader(f"Señal en el Tiempo: {seleccion}")
    fig_time = px.line(df_serie, x="fecha", y="afluencia", title="Serie Temporal Original")
    st.plotly_chart(fig_time, use_container_width=True)

    st.divider()

    # --- 2. CÁLCULO DE FOURIER (FFT) ---
    st.subheader("Gráfica de Amplitud Espectral")
    
    # Obtener valores de la señal
    y = df_serie["afluencia"].values
    n = len(y)
    
    # Restar la media para eliminar el componente DC
    y_detrend = y - np.mean(y)
    
    # Aplicar FFT
    yf = fft(y_detrend)
    xf = fftfreq(n, 1) # 1 = paso de muestreo (1 día)
    
    # Tomar solo la mitad positiva del espectro
    xf = xf[:n//2]
    magnitud = 2.0/n * np.abs(yf[0:n//2])
    
    # Crear DataFrame de resultados
    df_fft = pd.DataFrame({"Frecuencia": xf, "Potencia": magnitud})
    
    # Calcular el PERIODO (Días = 1 / Frecuencia)
    df_fft["Periodo (Dias)"] = df_fft["Frecuencia"].apply(lambda x: 1/x if x > 0 else 0)
    
    # Filtramos ruido (Frecuencias muy bajas o periodos infinitos)
    df_fft = df_fft[(df_fft["Frecuencia"] > 0.005) & (df_fft["Potencia"] > 100)]

    # Gráfica del Espectro
    fig_fft = px.bar(
        df_fft, 
        x="Periodo (Dias)", 
        y="Potencia", 
        title="Amplitud Espectral (Fuerza de los Ciclos)",
        labels={"Potencia": "Amplitud", "Periodo (Dias)": "Periodo del Ciclo (Dias)"}
    )
    # Ajustamos el eje X para ver mejor los ciclos cortos (semanales)
    fig_fft.update_layout(xaxis_range=[0, 35]) 
    st.plotly_chart(fig_fft, use_container_width=True)

    # --- 3. RESULTADOS E INTERPRETACION ---
    if not df_fft.empty:
        idx_max = df_fft["Potencia"].idxmax()
        ciclo_top = df_fft.loc[idx_max, "Periodo (Dias)"]
        
        # Tarjeta del dato principal
        st.metric("Ciclo Principal ", f"Cada {ciclo_top:.1f} Dias")
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
