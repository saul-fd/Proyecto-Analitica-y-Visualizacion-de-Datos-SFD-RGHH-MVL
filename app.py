import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import os
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.manifold import MDS, LocallyLinearEmbedding
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score, pairwise_distances

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(
    page_title="Analítica Metrobús CDMX",
    page_icon="🚌",
    layout="wide"
)

# --- FUNCIÓN DE CARGA DE DATOS (AUTOMÁTICA) ---
@st.cache_data
def cargar_datos():
    # Nombre del archivo hardcodeado según tu requerimiento
    archivo_csv = "afluencia-mb-2025.csv"
    
    # Verificar si el archivo existe en la ruta local
    if not os.path.exists(archivo_csv):
        return None, f"No se encontró el archivo '{archivo_csv}' en el directorio actual."
    
    try:
        df = pd.read_csv(archivo_csv)
        
        # --- LIMPIEZA BÁSICA ---
        # Convertir fecha si existe la columna
        # Ajusta 'fecha' al nombre real de tu columna de tiempo
        for col in ['fecha', 'Fecha', 'FECHA']:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col])
                break
                
        return df, None
    except Exception as e:
        return None, f"Error al leer el archivo: {e}"

# --- FUNCIÓN PARA PREPROCESAR DATOS PARA ML ---
def preparar_datos_ml(df, col_agrupacion, col_valor):
    # Agrupamos por la entidad de interés y calculamos métricas
    # Esto crea un perfil estadístico para cada línea/estación
    df_grouped = df.groupby(col_agrupacion)[col_valor].agg(['mean', 'std', 'min', 'max', 'sum']).reset_index()
    
    # Normalización (StandardScaler es crucial para PCA y Clustering)
    features = ['mean', 'std', 'min', 'max', 'sum']
    x = df_grouped.loc[:, features].values
    scaler = StandardScaler()
    x_scaled = scaler.fit_transform(x)
    
    return df_grouped, x_scaled

# --- INTERFAZ PRINCIPAL ---

st.title("📊 Dashboard de Analítica: Metrobús CDMX")
st.markdown("""
**Proyecto de Visualización y Análisis de Datos** Este dashboard carga automáticamente los datos locales para analizar afluencia, similitud y agrupamientos.
""")

# Intentar cargar los datos automáticamente
df, error_msg = cargar_datos()

if error_msg:
    st.error("⚠️ Error Crítico:")
    st.error(error_msg)
    st.info("Por favor, asegúrate de que el archivo 'afluencia-mb-2025.csv' esté en la misma carpeta que este script.")

elif df is not None:
    # Sidebar para configuración de columnas (para hacer el código flexible)
    st.sidebar.title("Configuración de Variables")
    st.sidebar.info("Datos cargados correctamente.")
    
    # Selectores para que indiques qué columnas usar
    col_linea = st.sidebar.selectbox(
        "Columna de Categoría (ej. Linea/Estación)", 
        options=[c for c in df.columns if df[c].dtype == 'object'],
        index=0
    )
    col_afluencia = st.sidebar.selectbox(
        "Columna Numérica (ej. Afluencia)", 
        options=df.select_dtypes(include=np.number).columns,
        index=0
    )
    
    # Preparamos los datos una sola vez
    df_ml, matrix_scaled = preparar_datos_ml(df, col_linea, col_afluencia)

    # Pestañas
    tab1, tab2, tab3, tab4 = st.tabs(["Exploración", "Matrices de Distancia", "PCA & Proyección", "Clustering (K-Means)"])
    
    # --- TAB 1: EXPLORACIÓN ---
    with tab1:
        st.header("Exploración Descriptiva")
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Registros Totales", len(df))
        col2.metric("Afluencia Total", f"{df[col_afluencia].sum():,.0f}")
        col3.metric("Entidades Únicas", df[col_linea].nunique())

        st.subheader("Muestra de Datos")
        st.dataframe(df.head())
        
        st.subheader(f"Distribución por {col_linea}")
        # Agrupamos para el gráfico de barras para no saturar si hay muchos datos
        df_chart = df.groupby(col_linea)[col_afluencia].sum().reset_index().sort_values(col_afluencia, ascending=False)
        fig_bar = px.bar(df_chart, x=col_linea, y=col_afluencia, title="Afluencia Total Acumulada")
        st.plotly_chart(fig_bar, use_container_width=True)

    # --- TAB 2: MATRICES ---
    with tab2:
        st.header("Análisis de Similitud")
        
        tipo_distancia = st.radio("Selecciona métrica:", ["Euclidiana", "Coseno", "Correlación"], horizontal=True)
        
        if tipo_distancia == "Euclidiana":
            matriz = pairwise_distances(matrix_scaled, metric='euclidean')
            title = "Distancia Euclidiana (Menor valor = Más similar)"
            colors = 'Viridis'
        elif tipo_distancia == "Coseno":
            matriz = pairwise_distances(matrix_scaled, metric='cosine')
            title = "Distancia Coseno (Menor valor = Más similar en dirección)"
            colors = 'Cividis'
        else:
            matriz = np.corrcoef(matrix_scaled)
            title = "Correlación de Pearson (1 = Idéntico comportamiento)"
            colors = 'RdBu'
        
        fig_heat = px.imshow(
            matriz, 
            x=df_ml[col_linea], 
            y=df_ml[col_linea],
            color_continuous_scale=colors,
            title=title,
            aspect="auto"
        )
        st.plotly_chart(fig_heat, use_container_width=True)

    # --- TAB 3: PCA / MDS ---
    with tab3:
        st.header("Reducción de Dimensionalidad")
        
        col_metodo, col_vacio = st.columns([1, 3])
        metodo = col_metodo.selectbox("Algoritmo", ["PCA", "MDS", "LLE"])
        
        if metodo == "PCA":
            model = PCA(n_components=2)
            proyeccion = model.fit_transform(matrix_scaled)
            info_extra = f"Varianza explicada: {np.sum(model.explained_variance_ratio_):.2%}"
        elif metodo == "MDS":
            model = MDS(n_components=2, random_state=42, normalized_stress='auto')
            proyeccion = model.fit_transform(matrix_scaled)
            info_extra = "Multidimensional Scaling"
        elif metodo == "LLE":
            model = LocallyLinearEmbedding(n_components=2, random_state=42)
            proyeccion = model.fit_transform(matrix_scaled)
            info_extra = "Locally Linear Embedding"

        st.caption(info_extra)
        
        df_proyeccion = pd.DataFrame(proyeccion, columns=['C1', 'C2'])
        df_proyeccion['Etiqueta'] = df_ml[col_linea]
        df_proyeccion['Tamaño'] = df_ml['sum'] # Tamaño basado en afluencia total

        fig_pca = px.scatter(
            df_proyeccion, x='C1', y='C2', 
            text='Etiqueta', 
            size='Tamaño',
            color='Etiqueta',
            title=f"Mapa de Similitud ({metodo})",
            hover_data=['Etiqueta']
        )
        fig_pca.update_traces(textposition='top center')
        st.plotly_chart(fig_pca, use_container_width=True)

    # --- TAB 4: CLUSTERING ---
    with tab4:
        st.header("Agrupamiento Automático (K-Means)")
        
        k = st.slider("Número de Clusters (k)", 2, 8, 3)
        
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        clusters = kmeans.fit_predict(matrix_scaled)
        
        # Guardar resultados
        df_ml['Cluster'] = clusters.astype(str)
        
        # Métricas
        sil = silhouette_score(matrix_scaled, clusters)
        st.info(f"Calidad del agrupamiento (Silhouette Score): {sil:.3f} (Más cercano a 1 es mejor)")
        
        # Visualización en espacio PCA
        pca_viz = PCA(n_components=2)
        coords = pca_viz.fit_transform(matrix_scaled)
        df_viz = pd.DataFrame(coords, columns=['x', 'y'])
        df_viz['Cluster'] = df_ml['Cluster']
        df_viz['Nombre'] = df_ml[col_linea]
        
        fig_clus = px.scatter(
            df_viz, x='x', y='y', 
            color='Cluster', 
            symbol='Cluster',
            hover_name='Nombre',
            title=f"Clusters visualizados en 2D (K={k})",
            template="plotly_white"
        )
        fig_clus.update_traces(marker=dict(size=12, line=dict(width=1, color='DarkSlateGrey')))
        st.plotly_chart(fig_clus, use_container_width=True)
        
        st.subheader("Estadísticas por Cluster")
        st.write("Promedio de las características por cada grupo:")
        st.dataframe(df_ml.groupby('Cluster')[['mean', 'std', 'min', 'max', 'sum']].mean().style.highlight_max(axis=0))s