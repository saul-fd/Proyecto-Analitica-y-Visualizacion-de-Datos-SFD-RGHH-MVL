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

# --- ESTILOS CSS (Minimalista) ---
st.markdown("""
<style>
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
    div[data-testid="stImage"] {
        display: flex;
        justify-content: center;
    }
    div[data-testid="stImage"] img {
        object-fit: contain;
    }
</style>
""", unsafe_allow_html=True)

# --- COLORES OFICIALES Y DICCIONARIO DE IMAGENES ---
# Usamos rutas relativas simples, pero las validamos con os.path
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

# Colores corregidos (Oficiales CDMX)
COLOR_MAP = {
    'Línea 1': '#B5261E', # Rojo Oscuro
    'Línea 2': '#6A1B9A', # Morado
    'Línea 3': '#7CB342', # Verde Limón
    'Línea 4': '#EF6C00', # Naranja
    'Línea 5': '#0288D1', # Azul Claro
    'Línea 6': '#D81B60', # Rosa Mexicano
    'Línea 7': '#2E7D32', # Verde Bandera
    'Emergente': '#616161' # Gris
}

# --- FUNCION PARA RESOLVER RUTAS DE IMAGENES ---
def get_img_path(filename):
    """
    Construye la ruta absoluta para evitar errores de 'File not found'
    incluso si ejecutas streamlit desde otra carpeta.
    """
    # Directorio base donde está este archivo app.py
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Intento 1: Carpeta 'imagenes' junto a app.py
    path_imagenes = os.path.join(base_dir, "imagenes", filename)
    if os.path.exists(path_imagenes):
        return path_imagenes
        
    # Intento 2: Mismo directorio que app.py
    path_root = os.path.join(base_dir, filename)
    if os.path.exists(path_root):
        return path_root
        
    return None

# --- FUNCION DE NORMALIZACION ---
def normalizar_linea(texto):
    """Ayuda a que 'Linea 1' coincida con 'Línea 1'"""
    if not isinstance(texto, str): return str(texto)
    # Reemplazo simple para asegurar coincidencia con las llaves del diccionario
    t = texto.strip().title() # Convierte a 'Línea 1'
    if "Linea" in t and "Línea" not in t:
        t = t.replace("Linea", "Línea")
    return t

# --- RENDERIZADO DEL HEADER ---
def render_header(df):
    if df.empty: return

    # Calculos generales
    dias = df["fecha"].nunique() or 1
    promedio_gral = df["afluencia"].sum() / dias
    
    # Agrupar por linea
    df_lineas = df.groupby("linea")["afluencia"].sum().reset_index()
    df_lineas["promedio"] = df_lineas["afluencia"] / dias
    
    # Importante: Ordenar por número de línea para que salga L1, L2...
    df_lineas = df_lineas.sort_values("linea")

    # Columnas: Logo Sistema + Una por cada línea
    cols = st.columns(len(df_lineas) + 1)

    # 1. Tarjeta Sistema General
    with cols[0]:
        path = get_img_path("ícono-MB.png")
        if path:
            st.image(path, width=55)
        else:
            st.markdown("🚍")
            
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-value">{promedio_gral:,.0f}</div>
            <div class="metric-label">Sistema Total</div>
        </div>""", unsafe_allow_html=True)

    # 2. Tarjetas por Línea
    for idx, row in df_lineas.iterrows():
        nombre_original = row["linea"]
        nombre_norm = normalizar_linea(nombre_original) # Normalizamos para buscar en dict
        valor = row["promedio"]
        
        # Buscar imagen usando el nombre normalizado
        archivo = IMAGENES.get(nombre_norm, "ícono-MB.png")
        path_img = get_img_path(archivo)
        
        # Color para el texto (fallback)
        color = COLOR_MAP.get(nombre_norm, "#555")

        with cols[idx + 1]:
            # Intentar mostrar imagen
            if path_img:
                st.image(path_img, width=55)
            else:
                # Si falla la imagen, mostrar circulo de color
                st.markdown(f'<div style="background:{color};width:40px;height:40px;border-radius:50%;margin:0 auto;"></div>', unsafe_allow_html=True)

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

    # Normalizar columna 'linea' en el dataframe para evitar problemas de cruce
    if 'linea' in df.columns:
        df['linea'] = df['linea'].apply(normalizar_linea)

    # FILTROS
    st.sidebar.header("Filtros")
    min_d, max_d = df["fecha"].min(), df["fecha"].max()
    ini = st.sidebar.date_input("Inicio", min_d)
    fin = st.sidebar.date_input("Fin", max_d)

    mask = (df["fecha"].dt.date >= ini) & (df["fecha"].dt.date <= fin)
    df_f = df.loc[mask]

    if df_f.empty:
        st.warning("Sin datos.")
        return

    # HEADER (Métricas + Imágenes)
    st.markdown("###")
    render_header(df_f)
    st.markdown("---")

    # GRAFICAS
    c1, c2 = st.columns([2, 1])

    with c1:
        st.subheader("Tendencia Diaria")
        df_time = df_f.groupby(["fecha", "linea"])["afluencia"].sum().reset_index()
        fig1 = px.line(
            df_time, x="fecha", y="afluencia", color="linea",
            color_discrete_map=COLOR_MAP # Usar colores corregidos
        )
        fig1.update_layout(template="plotly_white", xaxis_title="", yaxis_title="Pasajeros", legend=dict(orientation="h", y=1.1))
        st.plotly_chart(fig1, use_container_width=True)

    with c2:
        st.subheader("Distribución")
        df_pie = df_f.groupby("linea")["afluencia"].sum().reset_index()
        fig2 = px.pie(
            df_pie, values="afluencia", names="linea",
            color="linea", color_discrete_map=COLOR_MAP,
            hole=0.6
        )
        fig2.update_layout(template="plotly_white", showlegend=False, margin=dict(t=20, b=20, l=20, r=20))
        fig2.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig2, use_container_width=True)

if __name__ == "__main__":
    main()
