import streamlit as st

# Importamos las vistas (asegúrate de haber creado la carpeta 'views' y los archivos __init__.py si es necesario, 
# o simplemente que 'views' sea una carpeta con los .py dentro)
from views.home import show_home
from views.lineas import show_lineas

# --- CONFIGURACIÓN GLOBAL ---
st.set_page_config(
    page_title="Tablero Metrobus CDMX",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- MENÚ DE NAVEGACIÓN ---
st.sidebar.title("Navegación")

# Usamos un radio button para elegir qué página ver
# Es simple, robusto y nunca falla.
pagina = st.sidebar.radio(
    "Ir a:", 
    ["Inicio (General)", "Detalle por Línea"],
    index=0
)

st.sidebar.divider()

# --- ENRUTADOR ---
if pagina == "Inicio (General)":
    show_home()
elif pagina == "Detalle por Línea":
    show_lineas()
