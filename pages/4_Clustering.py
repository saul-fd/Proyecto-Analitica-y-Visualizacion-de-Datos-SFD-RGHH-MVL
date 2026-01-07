import streamlit as st
import pandas as pd
import plotly.express as px
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
from utils import cargar_datos

# Configuración de la página
st.set_page_config(page_title="Clustering de Líneas", layout="wide")

st.title("🧩 Segmentación de Líneas (Clustering)")
st.markdown("""
Este módulo agrupa las líneas del Metrobús basándose en su comportamiento estadístico 
(volumen de usuarios, variabilidad diaria y picos máximos).
""")

# 1. Cargar datos usando tu utilidad
df = cargar_datos()

if df is not None:
    # --- PREPARACIÓN DE LOS DATOS (Feature Engineering) ---
    # Para clusterizar, no usamos los datos crudos por día, necesitamos 
    # resumir cada LÍNEA en una sola fila con sus características.
    
    # Agrupamos por línea y calculamos estadísticas clave
    df_features = df.groupby("linea")["afluencia"].agg(
        promedio_diario="mean",
        desviacion_estandar="std", # Mide qué tanto varía la afluencia
        total_acumulado="sum",
        pico_maximo="max"
    ).reset_index()

    # Llenamos nulos con 0 (por seguridad)
    df_features = df_features.fillna(0)

    # Escalamos los datos (Crucial para K-Means porque el 'total' es millones y 'promedio' miles)
    features_cols = ["promedio_diario", "desviacion_estandar", "total_acumulado", "pico_maximo"]
    X = df_features[features_cols]
    
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # --- CONFIGURACIÓN (SIDEBAR) ---
    with st.sidebar:
        st.header("Configuración del Modelo")
        k_clusters = st.slider("Número de Grupos (K)", min_value=2, max_value=6, value=3)
        st.info("Ajusta K para ver cómo se redistribuyen las líneas.")

    # --- MODELADO (K-MEANS) ---
    kmeans = KMeans(n_clusters=k_clusters, random_state=42, n_init=10)
    clusters = kmeans.fit_predict(X_scaled)
    
    # Guardamos el cluster asignado en nuestro dataframe
    df_features["Cluster"] = clusters.astype(str)

    # --- VISUALIZACIÓN (REDUCCIÓN A 2D con PCA) ---
    # Usamos PCA para "aplastar" las 4 dimensiones estadísticas en 2 para poder graficar
    pca = PCA(n_components=2)
    components = pca.fit_transform(X_scaled)
    
    df_features["PC1"] = components[:, 0]
    df_features["PC2"] = components[:, 1]

    # --- INTERFAZ VISUAL ---
    col_grafica, col_datos = st.columns([2, 1])

    with col_grafica:
        st.subheader("Mapa de Similitud")
        
        fig = px.scatter(
            df_features,
            x="PC1", 
            y="PC2",
            color="Cluster",
            text="linea",
            size="total_acumulado", # El tamaño de la burbuja es el volumen total
            hover_data=features_cols,
            title=f"Agrupamiento K-Means (K={k_clusters})",
            template="plotly_white"
        )
        # Ajustes visuales para que las etiquetas se lean bien
        fig.update_traces(textposition='top center', marker=dict(opacity=0.8, line=dict(width=1, color='DarkSlateGrey')))
        st.plotly_chart(fig, use_container_width=True)

    with col_datos:
        st.subheader("Métricas y Resumen")
        
        # Silhouette Score
        score = silhouette_score(X_scaled, clusters)
        st.metric("Calidad del Agrupamiento (Silhouette)", f"{score:.3f}")
        
        st.markdown("### Perfil de los Grupos")
        # Mostrar el promedio de cada característica por cluster
        resumen = df_features.groupby("Cluster")[features_cols].mean()
        st.dataframe(resumen.style.highlight_max(axis=0), use_container_width=True)

    st.divider()
    st.caption("Nota: Las coordenadas X/Y en el gráfico son Componentes Principales (PCA) que representan matemáticamente la varianza de los datos.")

else:
    st.error("No se pudieron cargar los datos. Revisa data/afluencia-mb-2025.csv")
