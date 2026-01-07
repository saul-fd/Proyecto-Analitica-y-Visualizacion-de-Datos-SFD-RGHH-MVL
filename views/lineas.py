import streamlit as st
import pandas as pd
import plotly.express as px
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from utils import cargar_datos

def show_correlacion():
    # Estilos CSS
    st.markdown("""
    <style>
        .stMetric { background-color: #f0f2f6; padding: 10px; border-radius: 5px; }
    </style>
    """, unsafe_allow_html=True)

    st.title("Correlacion, PCA y Clustering")
    st.markdown("""
    Este modulo unifica el analisis de relaciones lineales (Pearson) con la segmentacion automatica (Clustering).
    """)

    try:
        df = cargar_datos()
    except Exception as e:
        st.error(f"Error cargando datos: {e}")
        return

    # ==============================================================================
    # 1. ANALISIS DE CORRELACION (PEARSON)
    # ==============================================================================
    st.header("1. Matriz de Correlacion y Mapa de Calor")
    st.markdown("Identifica visualmente que lineas tienen comportamientos similares.")

    # Pivoteamos: Filas=Fechas, Columnas=Lineas
    df_pivot = df.pivot_table(index="fecha", columns="linea", values="afluencia", aggfunc="sum").fillna(0)

    # --- A) MAPA DE CALOR (HEATMAP) ---
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

    # --- B) COMPARATIVA DIRECTA (SCATTER) ---
    st.subheader("Comparativa Directa entre Lineas")
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
    st.info(f"Coeficiente de Correlacion: {r2:.4f}")

    st.divider()

    # ==============================================================================
    # 2. REDUCCION DE DIMENSIONES (PCA - SERIES DE TIEMPO)
    # ==============================================================================
    st.header("2. Mapa de Similitud (PCA Historico)")
    st.markdown("Este grafico agrupa las lineas segun la similitud de sus curvas de afluencia diarias.")

    # Transponer: Filas=Lineas, Columnas=Fechas
    X_ts = df_pivot.T 
    
    scaler_ts = StandardScaler()
    X_ts_scaled = scaler_ts.fit_transform(X_ts)

    pca_ts = PCA(n_components=2)
    components_ts = pca_ts.fit_transform(X_ts_scaled)

    df_pca_ts = pd.DataFrame(data=components_ts, columns=['PC1', 'PC2'], index=X_ts.index)
    df_pca_ts["Linea"] = df_pca_ts.index
    
    var_ts = pca_ts.explained_variance_ratio_.sum() * 100

    fig_pca_ts = px.scatter(
        df_pca_ts, x='PC1', y='PC2', 
        text='Linea', 
        color='Linea',
        size_max=20,
        template="plotly_white",
        title=f"PCA basado en Series de Tiempo (Varianza explicada: {var_ts:.1f}%)"
    )
    fig_pca_ts.update_traces(textposition='top center', marker=dict(size=15, line=dict(width=2, color='DarkSlateGrey')))
    fig_pca_ts.update_layout(showlegend=False)
    st.plotly_chart(fig_pca_ts, use_container_width=True)

    st.divider()

    # ==============================================================================
    # 3. SEGMENTACION (CLUSTERING K-MEANS)
    # ==============================================================================
    st.header("3. Segmentacion de Lineas (Clustering)")
    st.markdown("Agrupamiento basado en estadisticas clave (Promedio, Desviacion, Totales).")

    # Feature Engineering
    df_features = df.groupby("linea")["afluencia"].agg(
        promedio_diario="mean",
        desviacion_estandar="std",
        total_acumulado="sum",
        pico_maximo="max"
    ).reset_index().fillna(0)

    # Escalado
    features_cols = ["promedio_diario", "desviacion_estandar", "total_acumulado", "pico_maximo"]
    X_feat = df_features[features_cols]
    scaler_feat = StandardScaler()
    X_feat_scaled = scaler_feat.fit_transform(X_feat)

    # Configuracion K (Sidebar)
    k_clusters = st.sidebar.slider("Numero de Grupos (K-Means)", min_value=2, max_value=6, value=3)

    # Modelo K-Means
    kmeans = KMeans(n_clusters=k_clusters, random_state=42, n_init=10)
    clusters = kmeans.fit_predict(X_feat_scaled)
    df_features["Cluster"] = clusters.astype(str)

    # PCA para visualizar Clusters
    pca_feat = PCA(n_components=2)
    components_feat = pca_feat.fit_transform(X_feat_scaled)
    
    df_features["PC1"] = components_feat[:, 0]
    df_features["PC2"] = components_feat[:, 1]

    # Visualizacion
    c_cluster, c_data = st.columns([2, 1])

    with c_cluster:
        st.subheader("Mapa de Grupos Detectados")
        fig_cluster = px.scatter(
            df_features,
            x="PC1", 
            y="PC2",
            color="Cluster",
            text="linea",
            size="total_acumulado",
            hover_data=features_cols,
            title=f"K-Means (K={k_clusters}) sobre Perfil Estadistico",
            template="plotly_white"
        )
        fig_cluster.update_traces(textposition='top center', marker=dict(opacity=0.8, line=dict(width=1, color='DarkSlateGrey')))
        st.plotly_chart(fig_cluster, use_container_width=True)

    with c_data:
        st.subheader("Metricas")
        score = silhouette_score(X_feat_scaled, clusters)
        st.metric("Calidad (Silhouette)", f"{score:.3f}")
        
        st.markdown("#### Perfil Promedio")
        resumen = df_features.groupby("Cluster")[features_cols].mean()
        st.dataframe(resumen.style.highlight_max(axis=0), use_container_width=True)

show_correlacion()
