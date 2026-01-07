import streamlit as st

# --- IMPORTACIÓN DE VISTAS (MÓDULOS) ---
from views.home import show_home
from views.lineas import show_lineas
from views.correlacion import show_correlacion
from views.temporal import show_temporal

# --- CONFIGURACIÓN GLOBAL DE LA PÁGINA ---
# Esto debe ser lo primero que se ejecute en la app
st.set_page_config(
    page_title="Tablero Metrobus CDMX",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- MENÚ DE NAVEGACIÓN (SIDEBAR) ---
st.sidebar.title("Navegación")

# Selector de Vistas
pagina = st.sidebar.radio(
    "Ir a:", 
    [
        "Inicio (General)", 
        "Detalle por Línea", 
        "Correlación, PCA y Clustering",
        "Análisis Espectral (Fourier)"
    ],
    index=0
)

st.sidebar.divider()

# --- ENRUTADOR (ROUTER) ---
# Decide qué función ejecutar según la selección del usuario

if pagina == "Inicio (General)":
    show_home()

elif pagina == "Detalle por Línea":
    show_lineas()

elif pagina == "Correlación, PCA y Clustering":
    show_correlacion()

elif pagina == "Análisis Espectral (Fourier)":
    show_temporal()


