import streamlit as st
import pandas as pd
import plotly.express as px
import os
import base64
from utils import cargar_datos

# --- CONFIGURACION DE PAGINA ---
st.set_page_config(
    page_title="Tablero Metrobus CDMX",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- ESTILOS CSS ---
# Usamos Flexbox para centrar dinámicamente las tarjetas
st.markdown("""
<style>
    /* Contenedor flexible que centra las tarjetas */
    .metrics-container {
        display: flex;
        flex-wrap: wrap;
        justify-content: center; /* ESTO CENTRA LOS ELEMENTOS AL MEDIO */
        gap: 20px; /* Espacio entre tarjetas */
        margin-bottom: 20px;
        padding: 10px;
    }
    
    /* Tarjeta individual */
    .metric-card {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: flex-start;
        width: 100px; /* Ancho fijo para uniformidad */
        text-align: center;
    }

    /* Imagen */
    .metric-img {
        height: 50px;
        width: auto;
        object-fit: contain;
        margin-bottom: 5px;
    }
    
    /* Valores y Textos */
    .metric-value {
        font-size: 20px;
        font-weight: 800;
        color: #ffffff; /* BLANCO (Según tu petición previa) */
        line-height: 1.2;
    }
    .metric-label {
        font-size: 11px;
        font-weight: 700;
        color: #e0e0e0; /* Gris claro */
        text-transform: uppercase;
        margin-top: 2px;
    }
    
    /* Fallback circular si no hay imagen */
    .circle-fallback {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        margin-bottom: 10px;
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

def img_to_base64(path):
    """Convierte imagen a string base64 para insertar en HTML"""
    if not path or not os.path.exists(path):
        return None
    with open(path, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()

def normalizar_linea(texto):
    if not isinstance(texto, str): return str(texto)
    t = texto.strip().title()
    if "Linea" in t and "Línea" not in t:
        t = t.replace("Linea", "Línea")
    return t

# --- RENDERIZADO HEADER (HTML PURO) ---
def render_header_html(df):
    if df.empty: return

    # Calculos
    dias = df["fecha"].nunique() or 1
    promedio_gral = df["afluencia"].sum() / dias
    
    df_lineas = df.groupby("linea")["afluencia"].sum().reset_index()
    df_lineas["promedio"] = df_lineas["afluencia"] / dias
    df_lineas = df_lineas.sort_values("linea")

    # Iniciar contenedor Flexbox
    html_content = '<div class="metrics-container">'

    # 1. TARJETA SISTEMA (Logo MB)
    path_mb = get_img_path("ícono-MB.png")
    b64_mb = img_to_base64(path_mb)
    
    img_tag_sys = ""
    if b64_mb:
        img_tag_sys = f'<img src="data:image/png;base64,{b64_mb}" class="metric-img">'
    else:
        img_tag_sys = '<div style="font-size:30px;">🚍</div>'

    html_content += f"""
        <div class="metric-card">
            {img_tag_sys}
            <div class="metric-value">{promedio_gral:,.0f}</div>
            <div class="metric-label">Sistema Total</div>
        </div>
    """

    # 2. TARJETAS POR LÍNEA
    for _, row in df_lineas.iterrows():
        nombre = normalizar_linea(row["linea"])
        valor = row["promedio"]
        
        archivo = IMAGENES.get(nombre, "ícono-MB.png")
        path_img = get_img_path(archivo)
        b64_img = img_to_base64(path_img)
        color = COLOR_MAP.get(nombre, "#555")

        img_tag = ""
        if b64_img:
            img_tag = f'<img src="data:image/png;base64,{b64_img}" class="metric-img">'
        else:
            img_tag = f'<div class="circle-fallback" style="background:{color};"></div>'

        html_content += f"""
        <div class="metric-card">
            {img_tag}
            <div class="metric-value">{valor:,.0f}</div>
            <div class="metric-label">{nombre.replace('Línea ', 'L')}</div>
        </div>
        """

    html_content += '</div>'
    
    # Renderizar HTML en Streamlit
    st.markdown(html_content, unsafe_allow_html=True)

# --- APP PRINCIPAL ---
def main():
    st.title("Tablero General de Afluencia")

    try:
        df = cargar_datos()
    except Exception as e:
        st.error(f"Error cargando datos: {e}")
        return

    if 'linea' in df.columns:
        df['linea'] = df['linea'].apply(normalizar_linea)

    # --- SIDEBAR ---
    st.sidebar.header("Filtros")
    min_d, max_d = df["fecha"].min(), df["fecha"].max()
    ini = st.sidebar.date_input("Inicio", min_d)
    fin = st.sidebar.date_input("Fin", max_d)
    st.sidebar.divider()

    # CHECKBOXES DE LÍNEAS
    st.sidebar.subheader("Líneas a visualizar")
    lineas_disponibles = sorted(df["linea"].unique())
    seleccion_lineas = []

    for linea in lineas_disponibles:
        if st.sidebar.checkbox(linea, value=True, key=f"chk_{linea}"):
            seleccion_lineas.append(linea)

    if not seleccion_lineas:
        st.warning("Selecciona al menos una línea.")
        return

    # APLICAR FILTROS
    mask = (
        (df["fecha"].dt.date >= ini) & 
        (df["fecha"].dt.date <= fin) & 
        (df["linea"].isin(seleccion_lineas))
    )
    df_f = df.loc[mask]

    if df_f.empty:
        st.warning("Sin datos.")
        return

    # HEADER (Flexbox HTML)
    st.markdown("###")
    render_header_html(df_f)
    st.markdown("---")

    # GRÁFICAS
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
            xaxis_title="", yaxis_title="Pasajeros",
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
