import streamlit as st
from views.home import show_home
from views.lineas import show_lineas

# --- CONFIGURACIÓN GLOBAL ---
# Se define una sola vez al principio de la app
st.set_page_config(
    page_title="Tablero Metrobus CDMX",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- MENÚ DE NAVEGACIÓN ---
st.sidebar.title("Navegación")

# Selector simple y robusto
pagina = st.sidebar.radio(
    "Ir a:", 
    ["Inicio (General)", "Detalle por Línea"],
    index=0
)

st.sidebar.divider()

# --- CONTROLADOR DE VISTAS ---
if pagina == "Inicio (General)":
    show_home()
elif pagina == "Detalle por Línea":
    show_lineas()
