import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import os
from scipy.fft import fft, fftfreq
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.manifold import MDS, LocallyLinearEmbedding
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score, pairwise_distances

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(
    page_title="Tablero de Control - Metrobús CDMX",
    page_icon="🚍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS personalizados para imitar tarjetas de KPI
st.markdown("""
<style>
    .kpi-card {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
        text-align: center;
        margin-bottom: 20px;
    }
    .kpi-value {
        font-size: 24px;
        font-weight: bold;
        color: #2c3e50;
    }
    .kpi-label {
        font-size: 14px;
        color: #7f8c8d;
    }
    div.block-container {padding-top: 1rem;}
</style>
""", unsafe_allow_html=True)

# --- CARGA DE DATOS ---
@st.cache_data
def cargar_datos():
    archivo_csv = "afluencia-mb-2025.csv"
    
    if not os.path.exists(archivo_csv):
        return None, f"No se encontró '{archivo_csv}'."
    
    try:
        df = pd.read_csv(archivo_csv)
        
        # Estandarización de nombres de columnas
        df.columns = [c.lower().strip() for c in df.columns]
        
        # Buscar columna de fecha
        col_fecha = next((c for c in df.columns if 'fecha' in c), None)
        if col_fecha:
            df[col_fecha] = pd.to_datetime(df[col_fecha])
            df['mes'] = df[col_fecha].dt.month_name(locale='es_ES') if 'month_name' in dir(df[col_fecha].dt) else df[col_fecha].dt.month
            df['dia_semana'] = df[col_fecha].dt.day_name(locale='es_ES') if 'day_name' in dir(df[col_fecha].dt) else df[col_fecha].dt.dayofweek
            df['dia_semana_num'] = df[col_fecha].dt.dayofweek
        
        return df, None
    except Exception as e:
        return None, str(e)

# --- FUNCIONES AUXILIARES ---
def tarjeta_kpi(col, titulo, valor, sufijo=""):
    col.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">{titulo}</div>
        <div class="kpi-value">{valor}{sufijo}</div>
    </div>
    """, unsafe_allow_html=True)

def preparar_datos_ml(df, col_agrupacion, col_valor):
    df_grouped = df.groupby(col_agrupacion)[col_valor].agg(['mean', 'std', 'min', 'max', 'sum']).reset_index()
    features = ['mean', 'std', 'min', 'max', 'sum']
    x = df_grouped.loc[:, features].values
    scaler = StandardScaler()
    x_scaled = scaler.fit_transform(x)
    return df_grouped, x_scaled

# --- INICIO DE LA APP ---
df, error = cargar_datos()

if df is not None:
    # Sidebar: Filtros Globales
    st.sidebar.header("🎛️ Filtros Globales")
    
    # Detección automática de columnas
    cols_numericas = df.select_dtypes(include=np.number).columns.tolist()
    cols_categ = df.select_dtypes(include='object').columns.tolist()
    col_fecha = next((c for c in df.columns if 'fecha' in c or 'date' in c), None)

    col_linea = st.sidebar.selectbox("Agrupar por (Categoría)", cols_categ, index=0)
    col_afluencia = st.sidebar.selectbox("Métrica de Afluencia", cols_numericas, index=0)
    
    # Filtro de fecha si existe
    df_filtrado = df.copy()
    if col_fecha:
        min_date, max_date = df[col_fecha].min(), df[col_fecha].max()
        dates = st.sidebar.date_input("Rango de Fechas", [min_date, max_date])
        if len(dates) == 2:
            df_filtrado = df[(df[col_fecha].dt.date >= dates[0]) & (df[col_fecha].dt.date <= dates[1])]

    # --- PESTAÑAS PRINCIPALES ---
    tab_general, tab_clustering, tab_espectral = st.tabs(["📊 Dashboard General", "🧩 Clustering & PCA", "〰️ Análisis Espectral"])

    # ==========================================
    # TAB 1: DASHBOARD GENERAL (Estilo MI Movilidad)
    # ==========================================
    with tab_general:
        st.subheader("Resumen Operativo")
        
        # KPIs Superiores
        total_afluencia = df_filtrado[col_afluencia].sum()
        promedio_diario = df_filtrado[col_afluencia].mean()
        max_afluencia = df_filtrado[col_afluencia].max()
        total_registros = len(df_filtrado)

        c1, c2, c3, c4 = st.columns(4)
        tarjeta_kpi(c1, "Viajes Totales (Periodo)", f"{total_afluencia:,.0f}")
        tarjeta_kpi(c2, "Promedio por Registro", f"{promedio_diario:,.0f}")
        tarjeta_kpi(c3, "Pico Máximo Registrado", f"{max_afluencia:,.0f}")
        tarjeta_kpi(c4, "Registros Analizados", f"{total_registros:,.0f}")

        # Gráficos Principales
        row1_col1, row1_col2 = st.columns([2, 1])
        
        with row1_col1:
            st.markdown("##### 📈 Evolución Diaria de Viajes")
            if col_fecha:
                diario = df_filtrado.groupby(col_fecha)[col_afluencia].sum().reset_index()
                fig_line = px.line(diario, x=col_fecha, y=col_afluencia, 
                                   template="plotly_white", height=350)
                fig_line.update_traces(line_color='#2980b9', line_width=2)
                st.plotly_chart(fig_line, use_container_width=True)
            else:
                st.warning("Se requiere columna de fecha para este gráfico.")

        with row1_col2:
            st.markdown("##### 🏆 Top Líneas/Estaciones")
            top_lineas = df_filtrado.groupby(col_linea)[col_afluencia].sum().nlargest(10).reset_index().sort_values(col_afluencia, ascending=True)
            fig_bar = px.bar(top_lineas, x=col_afluencia, y=col_linea, orientation='h',
                             template="plotly_white", height=350, color=col_afluencia, color_continuous_scale="Blues")
            fig_bar.update_layout(showlegend=False)
            st.plotly_chart(fig_bar, use_container_width=True)

        st.markdown("---")
        st.markdown("##### 📅 Mapa de Calor Mensual (Total de Viajes)")
        if col_fecha:
            # Heatmap Mes vs Línea
            df['mes_num'] = df[col_fecha].dt.month
            heatmap_data = df_filtrado.pivot_table(index=col_linea, columns='mes_num', values=col_afluencia, aggfunc='sum').fillna(0)
            
            fig_heat = px.imshow(heatmap_data, labels=dict(x="Mes", y="Línea", color="Afluencia"),
                                 x=['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'][:len(heatmap_data.columns)],
                                 aspect="auto", color_continuous_scale="Viridis")
            st.plotly_chart(fig_heat, use_container_width=True)

    # ==========================================
    # TAB 2: CLUSTERING & PCA
    # ==========================================
    with tab_clustering:
        st.subheader("Segmentación de Estaciones/Líneas")
        st.markdown("Agrupamiento basado en comportamiento estadístico (Promedio, Desviación, Máximos).")
        
        col_conf, col_viz = st.columns([1, 3])
        
        df_ml, matrix_scaled = preparar_datos_ml(df_filtrado, col_linea, col_afluencia)
        
        with col_conf:
            st.markdown("#### Configuración")
            k_clusters = st.slider("Número de Clusters (K)", 2, 8, 3)
            metodo_red = st.selectbox("Proyección 2D", ["PCA", "MDS"])
            
            # Cálculo K-Means
            kmeans = KMeans(n_clusters=k_clusters, random_state=42, n_init=10)
            clusters = kmeans.fit_predict(matrix_scaled)
            df_ml['Cluster'] = clusters.astype(str)
            
            score = silhouette_score(matrix_scaled, clusters)
            st.success(f"Silhouette Score: {score:.3f}")
            st.caption("Más cercano a 1 indica mejor separación.")

        with col_viz:
            # Reducción de Dimensionalidad para Visualización
            if metodo_red == "PCA":
                reducer = PCA(n_components=2)
                coords = reducer.fit_transform(matrix_scaled)
                title_viz = "Mapa de Clusters (PCA)"
            else:
                reducer = MDS(n_components=2, normalized_stress='auto', random_state=42)
                coords = reducer.fit_transform(matrix_scaled)
                title_viz = "Mapa de Clusters (MDS)"
                
            df_viz = pd.DataFrame(coords, columns=['x', 'y'])
            df_viz['Cluster'] = df_ml['Cluster']
            df_viz['Etiqueta'] = df_ml[col_linea]
            df_viz['Volumen'] = df_ml['sum']

            fig_clus = px.scatter(df_viz, x='x', y='y', color='Cluster', size='Volumen',
                                  hover_name='Etiqueta', title=title_viz, template="plotly_white",
                                  color_discrete_sequence=px.colors.qualitative.Bold)
            st.plotly_chart(fig_clus, use_container_width=True)

    # ==========================================
    # TAB 3: ANÁLISIS ESPECTRAL (FOURIER)
    # ==========================================
    with tab_espectral:
        st.subheader("🕵️ Análisis de Periodicidad (Fourier)")
        st.markdown("""
        Este módulo utiliza la **Transformada Rápida de Fourier (FFT)** para detectar patrones cíclicos en los datos.
        Se analiza el comportamiento promedio semanal para identificar si el ciclo dominante es de 7 días, 3.5 días, etc.
        """)
        
        if 'dia_semana_num' not in df.columns:
            st.error("Se requieren datos con fecha para realizar este análisis.")
        else:
            # Preparación de la señal
            orden_dias = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            # Mapeo simple si está en español o inglés, asumimos numérico 0-6 para ordenar
            df_sem = df_filtrado.groupby('dia_semana_num')[col_afluencia].mean().sort_index()
            
            # Generar señal artificial repetida (Simulación de onda continua)
            num_semanas = st.slider("Semanas a simular para análisis", 4, 52, 10)
            senal = np.tile(df_sem.values, num_semanas)
            
            c_fourier1, c_fourier2 = st.columns(2)
            
            with c_fourier1:
                st.markdown("##### 1. Señal de Afluencia Promedio (Repetida)")
                fig_signal = px.line(y=senal, x=range(len(senal)), title=f"Patrón Semanal Repetido ({num_semanas} veces)")
                fig_signal.update_layout(xaxis_title="Días simulados", yaxis_title="Afluencia Promedio")
                # Dibujar líneas verticales cada 7 días
                for i in range(0, len(senal), 7):
                    fig_signal.add_vline(x=i, line_dash="dash", line_color="red", opacity=0.3)
                st.plotly_chart(fig_signal, use_container_width=True)
            
            with c_fourier2:
                # Cálculo de FFT
                n = len(senal)
                fft_vals = fft(senal)
                fft_freqs = fftfreq(n, d=1) # d=1 día
                
                # Tomar solo la mitad positiva
                mitad = n // 2
                freqs = fft_freqs[:mitad]
                magnitud = np.abs(fft_vals[:mitad])
                
                # Filtrar frecuencia 0 (componente DC/Promedio constante)
                mask = freqs > 0
                freqs = freqs[mask]
                magnitud = magnitud[mask]
                
                # Normalizar magnitud
                magnitud = magnitud / np.max(magnitud)
                
                st.markdown("##### 2. Espectrograma de Frecuencias")
                fig_fft = px.bar(x=freqs, y=magnitud, title="Potencia por Frecuencia (Ciclos/Día)")
                fig_fft.update_layout(xaxis_title="Frecuencia (1/días)", yaxis_title="Magnitud Normalizada", xaxis_range=[0, 0.6])
                
                # Anotaciones de picos
                umbral = 0.2
                picos_idx = np.where(magnitud > umbral)[0]
                for idx in picos_idx:
                    f = freqs[idx]
                    periodo = 1/f
                    fig_fft.add_annotation(x=f, y=magnitud[idx], text=f"T={periodo:.1f}d", showarrow=True, arrowhead=1)
                
                st.plotly_chart(fig_fft, use_container_width=True)
            
            st.info(f"**Interpretación:** Si ves un pico alto en **0.14** (1/7), confirma un ciclo semanal fuerte. Un pico en **0.28** indica patrones de mitad de semana (3.5 días).")

else:
    st.error(error)
    st.info("Por favor verifica que el archivo 'afluencia-mb-2025.csv' esté en la carpeta.")
