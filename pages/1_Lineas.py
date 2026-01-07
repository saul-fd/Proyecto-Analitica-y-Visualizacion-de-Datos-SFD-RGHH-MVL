import streamlit as st
import plotly.express as px
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from utils import cargar_datos

# --- FUNCIÓN PRINCIPAL DE LA VISTA ---
def show_correlacion():
    # Estilos CSS específicos
    st.markdown("""
    <style>
        .stMetric { background-color: #f0f2f6; padding: 10px; border-radius: 5px; }
    </style>
    """, unsafe_allow_html=True)

    st.title("🔗 Correlación y Reducción de Dimensiones")
    st.markdown("""
    Este módulo analiza las relaciones estadísticas entre las líneas del Metrobús.
    """)

    try:
        df = cargar_datos()
    except Exception as e:
        st.error(f"Error cargando datos: {e}")
        return

    # PREPARACIÓN DE DATOS (Pivotear)
    # Filas = Fechas, Columnas = Líneas, Valores = Afluencia
    df_pivot = df.pivot_table(index="fecha", columns="linea", values="afluencia", aggfunc="sum").fillna(0)

    # --- SECCIÓN 1: MATRIZ DE PEARSON ---
    st.subheader("1. Matriz de Correlación (Pearson)")
    st.markdown("Identifica qué líneas tienen comportamientos temporales similares.")
    
    corr_matrix = df_pivot.corr(method='pearson')
    
    fig_heat = px.imshow(
        corr_matrix,
        text_auto=".2f",
        aspect="auto",
        color_continuous_scale="RdBu_r", # Rojo/Azul para contraste
        origin="lower",
        title="Mapa de Calor de Correlaciones"
    )
    st.plotly_chart(fig_heat, use_container_width=True)

    # --- SECCIÓN 2: COMPARATIVA DIRECTA ---
    st.subheader("2. Comparativa Directa (Scatter Plot)")
    c1, c2 = st.columns(2)
    with c1:
        x_axis = st.selectbox("Eje X", df_pivot.columns, index=0)
    with c2:
        y_axis = st.selectbox("Eje Y", df_pivot.columns, index=1)
        
    fig_scatter = px.scatter(
        df_pivot, x=x_axis, y=y_axis, 
        trendline="ols", # Regresión Lineal
        opacity=0.5,
        title=f"Relación: {x_axis} vs {y_axis}"
    )
    fig_scatter.update_traces(marker=dict(size=6, color="#2980b9"), line=dict(color="red"))
    st.plotly_chart(fig_scatter, use_container_width=True)
    
    r2 = df_pivot[x_axis].corr(df_pivot[y_axis])
    st.info(f"Coeficiente de Correlación: **{r2:.4f}** (Cercano a 1 indica fuerte similitud)")

    st.divider()

    # --- SECCIÓN 3: PCA (ANÁLISIS DE COMPONENTES PRINCIPALES) ---
    st.subheader("3. Mapa de Similitud (PCA)")
    st.markdown("""
    Usamos **PCA** para reducir la complejidad. Cada punto es una **Línea**.
    * **Puntos cercanos:** Líneas con patrones de afluencia muy parecidos.
    * **Puntos lejanos:** Líneas con comportamientos distintos.
    """)

    # Para PCA queremos agrupar LÍNEAS, así que transponemos la matriz
    # Filas = Líneas, Columnas = Fechas (Features)
    X = df_pivot.T 
    
    # 1. Estandarizar
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # 2. Aplicar PCA
    pca = PCA(n_components=2)
    components = pca.fit_transform(X_scaled)

    # 3. Crear DataFrame para graficar
    df_pca = pd.DataFrame(data=components, columns=['PC1', 'PC2'], index=X.index)
    df_pca["Linea"] = df_pca.index
    
    # Calcular varianza explicada (¿Qué tanto confiamos en este mapa?)
    var_explicada = pca.explained_variance_ratio_.sum() * 100

    col_pca, col_info = st.columns([3, 1])
    
    with col_pca:
        fig_pca = px.scatter(
            df_pca, x='PC1', y='PC2', 
            text='Linea', 
            color='Linea',
            size_max=20,
            template="plotly_white",
            title=f"Proyección PCA (Varianza explicada: {var_explicada:.1f}%)"
        )
        fig_pca.update_traces(textposition='top center', marker=dict(size=15, line=dict(width=2, color='DarkSlateGrey')))
        fig_pca.update_layout(showlegend=False)
        st.plotly_chart(fig_pca, use_container_width=True)

    with col_info:
        st.write("#### Interpretación")
        st.write(f"""
        Este gráfico reduce cientos de días de datos a solo 2 coordenadas.
        
        Las líneas agrupadas en el mismo cuadrante comparten **tendencias de usuarios, días pico y estacionalidad**.
        """)

show_correlacion()
