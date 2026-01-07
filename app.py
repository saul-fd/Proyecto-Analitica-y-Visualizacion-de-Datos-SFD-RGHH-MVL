import streamlit as st
import pandas as pd
import plotly.express as px
import os
from utils import cargar_datos

# --- CONFIGURACION DE PAGINA ---
st.set_page_config(
    page_title="Tablero Metrobus CDMX",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- ESTILOS CSS (Minimalista sin cuadros) ---
st.markdown("""
<style>
    /* Alineacion de metricas */
    .metric-container {
        text-align: center;
        padding: 10px 0;
    }
    .metric-value {
        font-size: 24px;
        font-weight: 800;
        color: #2c3e50;
        margin-top: 5px;
        line-height: 1.2;
    }
    .metric-label {
        font-size: 11px;
        font-weight: 600;
        color: #7f8c8d;
        text-transform: uppercase;
        margin-top: 2px;
    }
    /* Ajuste para las imagenes */
    div[data-testid="stImage"] {
        display: flex;
        justify-content: center;
    }
    div[data-testid="stImage"] img {
        object-fit: contain;
    }
</style>
""", unsafe_allow_html=True)

# --- CONFIGURACION DE RECURSOS ---
IMAGENES = {
    "Línea 1": "MB-1.png",
    "Línea 2": "MB-2.png",
    "Línea 3": "MB-3.png",
    "Línea 4": "MB-4.png",
    "Línea 5": "MB-5.png",
    "Línea 6": "MB-6.png",
    "Línea 7": "MB-7.png",
    "Emergente": "ícono-MB.png"
}

COLOR_MAP = {
    'Línea 1': '#B71C1C', 
    'Línea 2': '#4A148C', 
    'Línea 3': '#558B2F', 
    'Línea 4': '#E65100', 
    'Línea 5': '#0277BD', 
    'Línea 6': '#EC407A', 
    'Línea 7': '#2E7D32', 
    'Emergente': '#616161'
}

# --- FUNCION AUXILIAR: CARGAR IMAGEN ---
def get_image_path(filename):
    """Busca la imagen en la carpeta 'imagenes' o raiz"""
    paths = [
        os.path.join("imagenes", filename),
        filename
    ]
    for p in paths:
        if os.path.exists(p):
            return p
    return None

# --- RENDERIZADO DE METRICAS (HEADER) ---
def render_metrics_header(df_filtered):
    # 1. Calculos
    dias_unicos = df_filtered["fecha"].nunique()
    if dias_unicos == 0: dias_unicos = 1
    
    # Promedio Sistema
    promedio_sistema = df_filtered["afluencia"].sum() / dias_unicos
    
    # Promedios por Linea
    df_lineas = df_filtered.groupby("linea")["afluencia"].sum().reset_index()
    df_lineas["promedio"] = df_lineas["afluencia"] / dias_unicos
    df_lineas = df_lineas.sort_values("linea")

    # 2. Renderizado
    # Columnas: 1 (Logo MB) + N (Lineas)
    cols = st.columns(len(df_lineas) + 1)
    
    # A) Columna Sistema (Logo MB)
    with cols[0]:
        img_path = get_image_path("ícono-MB.png")
        if img_path:
            st.image(img_path, width=60)
        else:
            st.markdown("🚍") # Fallback texto
            
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-value">{promedio_sistema:,.0f}</div>
            <div class="metric-label">Sistema Total</div>
        </div>
        """, unsafe_allow_html=True)

    # B) Columnas Lineas
    for idx, row in df_lineas.iterrows():
        nombre = row["linea"]
        valor = row["promedio"]
        archivo_img = IMAGENES.get(nombre, "ícono-MB.png")
        
        with cols[idx + 1]:
            # Imagen
            img_path = get_image_path(archivo_img)
            if img_path:
                st.image(img_path, width=60)
            else:
                # Circulo de color si falla la imagen
                color = COLOR_MAP.get(nombre, "#999")
                st.markdown(f'<div style="background:{color};width:40px;height:40px;border-radius:50%;margin:0 auto;"></div>', unsafe_allow_html=True)

            # Dato
            st.markdown(f"""
            <div class="metric-container">
                <div class="metric-value">{valor:,.0f}</div>
                <div class="metric-label">{nombre.replace('Línea ', 'L')}</div>
            </div>
            """, unsafe_allow_html=True)

# --- APP PRINCIPAL ---
def main():
    st.title("Tablero General de Afluencia")
    
    try:
        df = cargar_datos()
    except Exception as e:
        st.error(f"Error cargando datos: {e}")
        return

    # Sidebar: Filtros
    st.sidebar.header("Filtros")
    min_date, max_date = df["fecha"].min(), df["fecha"].max()
    start = st.sidebar.date_input("Inicio", min_date)
    end = st.sidebar.date_input("Fin", max_date)
    
    # Aplicar filtro de fecha
    mask = (df["fecha"].dt.date >= start) & (df["fecha"].dt.date <= end)
    df_filtered = df.loc[mask]

    if df_filtered.empty:
        st.warning("Sin datos en este rango.")
        return

    # 1. HEADER VISUAL (Imagenes + Datos)
    st.markdown("###")
    render_metrics_header(df_filtered)
    st.markdown("---")

    # 2. GRAFICAS
    c1, c2 = st.columns([2, 1])

    with c1:
        st.subheader("Evolucion Diaria")
        df_time = df_filtered.groupby(["fecha", "linea"])["afluencia"].sum().reset_index()
        fig_line = px.line(
            df_time, x="fecha", y="afluencia", color="linea",
            color_discrete_map=COLOR_MAP
        )
        fig_line.update_layout(
            template="plotly_white",
            hovermode="x unified",
            xaxis_title="", yaxis_title="Pasajeros",
            legend=dict(orientation="h", y=1.1)
        )
        st.plotly_chart(fig_line, use_container_width=True)

    with c2:
        st.subheader("Distribucion Total")
        df_pie = df_filtered.groupby("linea")["afluencia"].sum().reset_index()
        fig_pie = px.pie(
            df_pie, values="afluencia", names="linea",
            color="linea", color_discrete_map=COLOR_MAP,
            hole=0.5
        )
        fig_pie.update_layout(
            template="plotly_white",
            showlegend=False,
            margin=dict(t=20, b=20, l=20, r=20)
        )
        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_pie, use_container_width=True)

if __name__ == "__main__":
    main()
