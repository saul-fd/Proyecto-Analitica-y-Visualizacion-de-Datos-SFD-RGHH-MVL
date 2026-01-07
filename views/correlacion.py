import streamlit as st
import pandas as pd
import plotly.express as px
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from utils import cargar_datos

def show_correlacion():
    # --- SE ELIMINÓ EL BLOQUE DE ESTILOS CSS QUE CAUSABA EL FONDO BLANCO ---

    st.title("Correlacion y Agrupamiento")
    st.markdown("""
    Este modulo analiza la relacion entre lineas y las agrupa segun su comportamiento estadistico.
    """)

    try:
        df = cargar_datos()
    except Exception as e:
        st.error(f"Error cargando datos: {e}")
        return

    # ==============================================================================
    # 1. ANALISIS DE CORRELACION (PEARSON)
    # ==============================================================================
    st.header("Matriz de Correlacion")
    st.markdown("Analisis de la relacion lineal entre las diferentes lineas.")

    # Pivoteamos: Filas=Fechas, Columnas=Lineas
    df_pivot = df.pivot_table(index="fecha", columns="linea", values="afluencia", aggfunc="sum").fillna(0)

    # --- MAPA DE CALOR (HEATMAP) ---
    corr_matrix = df_pivot.corr(method='pearson')
    
    fig_heat = px.imshow(
        corr_matrix,
        text_auto=".2f",
        aspect="auto",
        color_continuous_scale="RdBu_r", # Escala Rojo-Azul
        origin="lower",
        title="Mapa de Calor de Correlaciones (Pearson)"
    )
    st.plotly_chart(fig_heat, use_container_width=True)

    # --- COMPARATIVA DIRECTA (SCATTER) ---
    st.subheader("Comparativa Directa")
    col1, col2 = st.columns(2)
    with col1:
        x_axis = st.selectbox("Eje X", df_pivot.columns, index=0)
    with col2:
        y_axis = st.selectbox("Eje Y", df_pivot.columns, index=1)
        
    fig_scatter = px.scatter(
        df_pivot, x=x_axis, y=y_axis, 
        trendline="ols",
        opacity=0.5,
        title=f"Dispersion: {x_axis} vs {y_axis}"
    )
    fig_scatter.update_traces(marker=dict(size=6, color="#2980b9"), line=dict(color="red"))
    st.plotly_chart(fig_scatter, use_container_width=True)
    
    r2 = df_pivot[x_axis].corr(df_pivot[y_axis])
    st.info(f"Coeficiente de Correlacion (R): {r2:.4f}")

    st.divider()

    # ==============================================================================
    # 2. PCA CON CLUSTERING (SEGMENTACION)
    # ==============================================================================
    st.header("Segmentacion de Lineas (PCA + K-Means)")
    st.markdown("""
    Agrupamiento de lineas basado en sus caracteristicas estadisticas (Promedio, Desviacion, Totales).
    Se utiliza PCA para visualizar los grupos en 2 dimensiones.
    """)

    # --- PREPARACION DE CARACTERISTICAS (FEATURE ENGINEERING) ---
    df_features = df.groupby("linea")["afluencia"].agg(
        promedio_diario="mean",
        desviacion_estandar="std",
        total_acumulado="sum",
        pico_maximo="max"
    ).reset_index().fillna(0)

    # Escalado de datos (Necesario para PCA y K-Means)
    features_cols = ["promedio_diario", "desviacion_estandar", "total_acumulado", "pico_maximo"]
    X = df_features[features_cols]
    
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # --- CONFIGURACION K-MEANS ---
    k_clusters = st.sidebar.slider("Numero de Grupos (K-Means)", min_value=2, max_value=6, value=3)

    # --- MODELADO (CLUSTERING) ---
    kmeans = KMeans(n_clusters=k_clusters, random_state=42, n_init=10)
    clusters = kmeans.fit_predict(X_scaled)
    df_features["Cluster"] = clusters.astype(str)

    # --- REDUCCION DE DIMENSIONES (PCA) PARA VISUALIZACION ---
    pca = PCA(n_components=2)
    components = pca.fit_transform(X_scaled)
    
    # Agregamos las coordenadas PCA al dataframe
    df_features["PC1"] = components[:, 0]
    df_features["PC2"] = components[:, 1]
    
    var_explicada = pca.explained_variance_ratio_.sum() * 100

    # --- VISUALIZACION ---
    c_grafica, c_datos = st.columns([2, 1])

    with c_grafica:
        st.subheader("Mapa de Grupos (PCA)")
        fig_pca = px.scatter(
            df_features,
            x="PC1", 
            y="PC2",
            color="Cluster",
            text="linea",
            size="total_acumulado",
            hover_data=features_cols,
            title=f"Proyeccion PCA con Clustering K-Means (Varianza: {var_explicada:.1f}%)",
            template="plotly_white"
        )
        fig_pca.update_traces(textposition='top center', marker=dict(opacity=0.8, line=dict(width=1, color='DarkSlateGrey')))
        st.plotly_chart(fig_pca, use_container_width=True)

    with c_datos:
        st.subheader("Metricas y Resumen")
        
        # Silhouette Score
        score = silhouette_score(X_scaled, clusters)
        st.metric("Calidad Agrupamiento (Silhouette)", f"{score:.3f}")
        
        st.markdown("#### Promedios por Grupo")
        # Mostrar caracteristicas promedio de cada cluster
        resumen = df_features.groupby("Cluster")[features_cols].mean()
        st.dataframe(resumen.style.highlight_max(axis=0), use_container_width=True)
