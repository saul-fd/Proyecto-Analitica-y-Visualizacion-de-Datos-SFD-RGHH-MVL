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

# --- ESTILOS CSS (Centrado Agresivo) ---
st.markdown("""
<style>
    /* Forzar el centrado de todo el contenido dentro de las columnas */
    [data-testid="column"] {
        display: flex;
        flex-direction: column;
        align-items: center;
        text-align: center;
        justify-content: flex-start;
    }
    
    /* Ajuste para las metricas */
    .metric-container {
        width: 100%;
        text-align: center;
        margin-top: 5px;
    }
    .metric-value {
        font-size: 22px;
        font-weight: 800;
        color: #2c3e50;
        line-height: 1.2;
    }
    .metric-label {
        font-size: 11px;
        font-weight: 700;
        color: #7f8c8d;
        text-transform: uppercase;
        margin-top: 2px;
    }
    
    /* Asegurar que las imagenes no se estiren y esten centradas */
    div[data-testid="stImage"] {
        display: flex;
        justify-content: center;
        width: 100%;
    }
    div[data-testid="stImage"] img {
        object-fit: contain;
        max-height: 60px; /* Control de altura para uniformidad */
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
    'Línea 1': '#B5261E', 
    'Línea 2': '#6A1B9A', 
    'Línea 3': '#7CB342', 
    'Línea 4': '#EF6C00', 
    'Línea 5': '#0288D1', 
    'Línea 6': '#D81B60', 
    'Línea 7': '#2E7D32', 
    'Emergente': '#616161'
}

# --- FUNCIONES AUXILIARES ---
def get_img_path(filename):
    """Resuelve la ruta absoluta de la imagen"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    paths = [
        os.path.join(base_dir, "imagenes", filename),
        os.path.join(base_dir, filename)
    ]
    for p in paths:
        if os.path.exists(p):
            return p
    return None

def normalizar_linea(texto):
    """Normaliza nombres como 'Linea 1' a 'Línea 1' para coincidir con imagenes"""
    if not isinstance(texto, str): return str(texto)
    t = texto.strip().title()
    if "Linea" in t and "Línea" not in t:
        t = t.replace("Linea", "Línea")
    return t

# --- RENDERIZADO HEADER ---
def render_header(df):
    if df.empty: return

    # Datos Generales
    dias = df["fecha"].nunique() or 1
    promedio_gral = df["afluencia"].sum() / dias
    
    # Datos por Linea
    df_lineas = df.groupby("linea")["afluencia"].sum().reset_index()
    df_lineas["promedio"] = df_lineas["afluencia"] / dias
    df_lineas = df_lineas.sort_values("linea")

    # Crear columnas (1 para Sistema + N para líneas)
    cols = st.columns(len(df_lineas) + 1)

    # 1. Sistema Total
    with cols[0]:
        path = get_img_path("ícono-MB.png")
        if path:
            st.image(path, width=50)
        else:
            st.markdown("🚍")
            
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-value">{promedio_gral:,.0f}</div>
            <div class="metric-label">Sistema Total</div>
        </div>""", unsafe_allow_html=True)

    # 2. Iterar Líneas
    for idx, row in df_lineas.iterrows():
        nombre_norm = normalizar_linea(row["linea"])
        valor = row["promedio"]
        archivo = IMAGENES.get(nombre_norm, "ícono-MB.png")
        path_img = get_img_path(archivo)
        color = COLOR_MAP.get(nombre_norm, "#555")

        with cols[idx + 1]:
            # Imagen
            if path_img:
                st.image(path_img, width=50)
            else:
                st.markdown(f'<div style="background:{color};width:40px;height:40px;border-radius:50%;margin-bottom:10px;"></div>', unsafe_allow_html=True)

            # Texto
            st.markdown(f"""
            <div class="metric-container">
                <div class="metric-value">{valor:,.0f}</div>
                <div class="metric-label">{nombre_norm.replace('Línea ', 'L')}</div>
            </div>""", unsafe_allow_html=True)

# --- APP PRINCIPAL ---
def main():
    st.title("Tablero General de Afluencia")

    try:
        df = cargar_datos()
    except Exception as e:
        st.error(f"Error cargando datos: {e}")
        return

    # Normalizacion de datos
    if 'linea' in df.columns:
        df['linea'] = df['linea'].apply(normalizar_linea)

    # --- BARRA LATERAL: FILTROS ---
    st.sidebar.header("Filtros")
    
    # 1. Filtro Fecha
    min_d, max_d = df["fecha"].min(), df["fecha"].max()
    ini = st.sidebar.date_input("Inicio", min_d)
    fin = st.sidebar.date_input("Fin", max_d)
    
    st.sidebar.divider()

    # 2. Filtro Línea (Multiselect)
    lineas_disponibles = sorted(df["linea"].unique())
    seleccion_lineas = st.sidebar.multiselect(
        "Filtrar Líneas",
        options=lineas_disponibles,
        default=lineas_disponibles # Todas seleccionadas al inicio
    )

    # Validar seleccion
    if not seleccion_lineas:
        st.warning("⚠️ Por favor selecciona al menos una línea para visualizar los datos.")
        return

    # Aplicar Filtros (Fecha + Línea)
    mask = (
        (df["fecha"].dt.date >= ini) & 
        (df["fecha"].dt.date <= fin) & 
        (df["linea"].isin(seleccion_lineas))
    )
    df_f = df.loc[mask]

    if df_f.empty:
        st.warning("Sin datos para los filtros seleccionados.")
        return

    # Header
    st.markdown("###")
    render_header(df_f)
    st.markdown("---")

    # Gráficas
    c1, c2 = st.columns([2, 1])

    with c1:
        st.subheader("Tendencia Diaria")
        df_time = df_f.groupby(["fecha", "linea"])["afluencia"].sum().reset_index()
        fig1 = px.line(
            df_time, x="fecha", y="afluencia", color="linea",
            color_discrete_map=COLOR_MAP
        )
        fig1.update_layout(
            template="plotly_white", 
            xaxis_title="", 
            yaxis_title="Pasajeros", 
            legend=dict(orientation="h", y=1.1, x=0.5, xanchor="center")
        )
        st.plotly_chart(fig1, use_container_width=True)

    with c2:
        st.subheader("Distribución")
        df_pie = df_f.groupby("linea")["afluencia"].sum().reset_index()
        fig2 = px.pie(
            df_pie, values="afluencia", names="linea",
            color="linea", color_discrete_map=COLOR_MAP,
            hole=0.6
        )
        fig2.update_layout(
            template="plotly_white", 
            showlegend=False, 
            margin=dict(t=20, b=20, l=20, r=20)
        )
        fig2.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig2, use_container_width=True)

if __name__ == "__main__":
    main()
