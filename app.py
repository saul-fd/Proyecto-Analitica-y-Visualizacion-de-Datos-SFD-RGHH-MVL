import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import os
from scipy.fft import fft, fftfreq
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.manifold import MDS
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(
    page_title="Sistema de Analítica Metrobús",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- ESTILOS CSS FORMALES (CORPORATE UI) ---
st.markdown("""
<style>
    /* Fondo general y fuentes */
    .reportview-container {
        background: #f0f2f6;
    }
    h1, h2, h3 {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        color: #2c3e50;
    }
    /* Estilo de Tarjetas KPI */
    .kpi-card {
        background-color: #ffffff;
        border-left: 5px solid #2980b9; /* Azul institucional */
        border-radius: 4px;
        padding: 20px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.12);
        margin-bottom: 20px;
    }
    .kpi-value {
        font-size: 28px;
        font-weight: 600;
        color: #2c3e50;
        margin-bottom: 5px;
    }
    .kpi-label {
        font-size: 13px;
        color: #7f8c8d;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    /* Ajuste de pestañas */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #ffffff;
        border-radius: 4px 4px 0px 0px;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #eef2f6;
        color: #2980b9;
        font-weight: bold;
        border-top: 3px solid #2980b9;
    }
</style>
""", unsafe_allow_html=True)

# --- CARGA DE DATOS ---
@st.cache_data
def cargar_datos():
    archivo_csv = "afluencia-mb-2025.csv"
    
    if not os.path.exists(archivo_csv):
        return None, f"Error: No se encontró el archivo '{archivo_csv}' en el directorio raíz."
    
    try:
        df = pd.read_csv(archivo_csv)
        
        # Normalización de cabeceras
        df.columns = [c.lower().strip() for c in df.columns]
        
        # Detección y conversión de fechas
        col_fecha = next((c for c in df.columns if 'fecha' in c), None)
        if col_fecha:
            df[col_fecha] = pd.to_datetime(df[col_fecha])
            # Generación de variables temporales
            df['mes'] = df[col_fecha].dt.month
            df['dia_semana_num'] = df[col_fecha].dt.dayofweek
        
        return df, None
    except Exception as e:
        return None, f"Excepción de lectura: {str(e)}"

# --- COMPONENTES UI ---
def tarjeta_kpi(col, titulo, valor):
    col.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-value">{valor}</div>
        <div class="kpi-label">{titulo}</div>
    </div>
    """, unsafe_allow_html=True)

def preparar_datos_ml(df, col_agrupacion, col_valor):
    # Agregación estadística
    df_grouped = df.groupby(col_agrupacion)[col_valor].agg(['mean', 'std', 'min', 'max', 'sum']).reset_index()
    features = ['mean', 'std', 'min', 'max', 'sum']
    
    # Escalado
    x = df_grouped.loc[:, features].values
    scaler = StandardScaler()
    x_scaled = scaler.fit_transform(x)
    return df_grouped, x_scaled

# --- LÓGICA PRINCIPAL ---
df, error_msg = cargar_datos()

st.title("Sistema de Análisis de Movilidad | Metrobús CDMX")
st.markdown("Plataforma de visualización de datos, segmentación y análisis espectral.")
st.divider()

if df is not None:
    # --- BARRA LATERAL (CONFIGURACIÓN) ---
    st.sidebar.title("Panel de Control")
    st.sidebar.markdown("---")
    
    # Selectores de Variables
    st.sidebar.subheader("Definición de Variables")
    cols_numericas = df.select_dtypes(include=np.number).columns.tolist()
    cols_categ = df.select_dtypes(include='object').columns.tolist()
    col_fecha = next((c for c in df.columns if 'fecha' in c), None)

    # Fallback si no hay categóricas detectadas
    if not cols_categ:
        cols_categ = [c for c in df.columns if c not in cols_numericas]

    col_linea = st.sidebar.selectbox("Dimensión Categórica (Ej. Línea/Estación)", cols_categ, index=0)
    col_afluencia = st.sidebar.selectbox("Métrica Numérica (Ej. Afluencia)", cols_numericas, index=0)
    
    # Filtro Temporal
    df_filtrado = df.copy()
    if col_fecha:
        st.sidebar.subheader("Filtro Temporal")
        min_date = df[col_fecha].min().date()
        max_date = df[col_fecha].max().date()
        dates = st.sidebar.date_input("Periodo de Análisis", [min_date, max_date])
        if len(dates) == 2:
            df_filtrado = df[(df[col_fecha].dt.date >= dates[0]) & (df[col_fecha].dt.date <= dates[1])]
    
    # --- PESTAÑAS ---
    tab1, tab2, tab3 = st.tabs(["Tablero General", "Clustering y PCA", "Análisis Espectral"])

    # 1. TABLERO GENERAL
    with tab1:
        st.header("Resumen Ejecutivo")
        
        # KPIs
        total_afluencia = df_filtrado[col_afluencia].sum()
        promedio = df_filtrado[col_afluencia].mean()
        max_val = df_filtrado[col_afluencia].max()
        registros = len(df_filtrado)

        c1, c2, c3, c4 = st.columns(4)
        tarjeta_kpi(c1, "Afluencia Total Acumulada", f"{total_afluencia:,.0f}")
        tarjeta_kpi(c2, "Promedio por Registro", f"{promedio:,.2f}")
        tarjeta_kpi(c3, "Valor Máximo Registrado", f"{max_val:,.0f}")
        tarjeta_kpi(c4, "Volumen de Datos (Filas)", f"{registros:,.0f}")

        # Gráficos
        col_izq, col_der = st.columns([2, 1])
        
        with col_izq:
            st.subheader("Evolución Temporal")
            if col_fecha:
                df_tiempo = df_filtrado.groupby(col_fecha)[col_afluencia].sum().reset_index()
                fig_line = px.line(df_tiempo, x=col_fecha, y=col_afluencia)
                fig_line.update_layout(template="plotly_white", xaxis_title="Fecha", yaxis_title="Afluencia")
                fig_line.update_traces(line_color='#2980b9')
                st.plotly_chart(fig_line, use_container_width=True)
            else:
                st.info("No se detectó columna de fecha para la serie temporal.")

        with col_der:
            st.subheader("Ranking por Categoría")
            df_rank = df_filtrado.groupby(col_linea)[col_afluencia].sum().nlargest(10).reset_index().sort_values(col_afluencia, ascending=True)
            fig_bar = px.bar(df_rank, x=col_afluencia, y=col_linea, orientation='h')
            fig_bar.update_layout(template="plotly_white", xaxis_title="Total", yaxis_title="")
            fig_bar.update_traces(marker_color='#34495e')
            st.plotly_chart(fig_bar, use_container_width=True)

    # 2. CLUSTERING
    with tab2:
        st.header("Segmentación Multivariable (Clustering)")
        st.markdown("Agrupamiento no supervisado basado en el perfil estadístico de cada elemento.")
        
        df_ml, matrix_scaled = preparar_datos_ml(df_filtrado, col_linea, col_afluencia)
        
        col_params, col_plot = st.columns([1, 3])
        
        with col_params:
            st.markdown("#### Configuración del Modelo")
            k = st.slider("Número de Clusters (K)", 2, 10, 3)
            algo_red = st.selectbox("Método de Proyección", ["PCA (Lineal)", "MDS (Distancia)"])
            
            # K-Means
            kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
            clusters = kmeans.fit_predict(matrix_scaled)
            df_ml['Cluster_ID'] = clusters.astype(str)
            
            sil = silhouette_score(matrix_scaled, clusters)
            st.metric("Coeficiente de Silhouette", f"{sil:.3f}", help="Medida de cohesión y separación (Máx 1.0)")

        with col_plot:
            # Reducción
            if algo_red.startswith("PCA"):
                model = PCA(n_components=2)
                coords = model.fit_transform(matrix_scaled)
                label_x, label_y = "Componente Principal 1", "Componente Principal 2"
            else:
                model = MDS(n_components=2, normalized_stress='auto', random_state=42)
                coords = model.fit_transform(matrix_scaled)
                label_x, label_y = "Dimensión 1", "Dimensión 2"

            df_viz = pd.DataFrame(coords, columns=['x', 'y'])
            df_viz['Cluster'] = df_ml['Cluster_ID']
            df_viz['Etiqueta'] = df_ml[col_linea]
            
            fig_clus = px.scatter(
                df_viz, x='x', y='y', color='Cluster', 
                hover_name='Etiqueta', 
                title=f"Distribución de Clusters ({algo_red})",
                template="plotly_white",
                color_discrete_sequence=px.colors.qualitative.G10
            )
            fig_clus.update_layout(xaxis_title=label_x, yaxis_title=label_y)
            st.plotly_chart(fig_clus, use_container_width=True)

    # 3. ESPECTRAL
    with tab3:
        st.header("Análisis Espectral (Transformada de Fourier)")
        st.markdown("Detección de ciclicidad y estacionalidad en la serie temporal mediante descomposición en el dominio de la frecuencia.")

        if 'dia_semana_num' in df.columns:
            # Preparación de señal promedio semanal
            df_week = df_filtrado.groupby('dia_semana_num')[col_afluencia].mean().sort_index()
            
            # Simulación
            col_sim, col_fft = st.columns([1, 1])
            with col_sim:
                st.subheader("Señal Sintética (Patrón Semanal)")
                n_weeks = st.slider("Ciclos a simular", 4, 52, 10)
                signal = np.tile(df_week.values, n_weeks)
                
                fig_sig = px.line(y=signal, title="Serie Temporal Reconstruida")
                fig_sig.update_layout(template="plotly_white", xaxis_title="Días", yaxis_title="Magnitud Promedio")
                st.plotly_chart(fig_sig, use_container_width=True)
            
            with col_fft:
                st.subheader("Espectrograma de Frecuencia")
                # FFT
                N = len(signal)
                yf = fft(signal)
                xf = fftfreq(N, d=1)[:N//2]
                magnitude = 2.0/N * np.abs(yf[0:N//2])
                
                # Excluir DC component (freq 0)
                mask = xf > 0.01
                xf_plot = xf[mask]
                mag_plot = magnitude[mask]
                
                fig_fft = px.bar(x=xf_plot, y=mag_plot)
                fig_fft.update_layout(
                    title="Densidad Espectral de Potencia",
                    xaxis_title="Frecuencia (1/días)",
                    yaxis_title="Amplitud",
                    template="plotly_white",
                    xaxis_range=[0, 0.5]
                )
                
                # Detección de picos
                threshold = np.max(mag_plot) * 0.3
                peaks_idx = np.where(mag_plot > threshold)[0]
                for p in peaks_idx:
                    freq_val = xf_plot[p]
                    period = 1 / freq_val
                    fig_fft.add_annotation(
                        x=freq_val, y=mag_plot[p],
                        text=f"T={period:.1f}d",
                        showarrow=True, arrowhead=2
                    )
                
                st.plotly_chart(fig_fft, use_container_width=True)
            
            st.info("Nota Técnica: Un periodo (T) de 7.0 días confirma una estacionalidad semanal fuerte. Valores cercanos a 3.5 indican sub-ciclos de media semana.")
            
        else:
            st.warning("No es posible realizar el análisis espectral: Datos temporales insuficientes.")

else:
    st.error(f"Error Crítico: {error_msg}")
    st.markdown("Verifique la ubicación del archivo fuente 'afluencia-mb-2025.csv'.")
