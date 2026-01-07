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

# --- ESTILOS CSS ---
st.markdown("""
<style>
    /* Centrar contenido dentro de las columnas de Streamlit */
    [data-testid="column"] {
        text-align: center;
        display: flex;
        flex-direction: column;
        align-items: center;
    }
    
    /* Estilos de Textos */
    .metric-value {
        font-size: 20px;
        font-weight: 800;
        color: #ffffff; /* BLANCO */
        margin-top: 5px;
        line-height: 1.2;
        text-shadow: 0px 1px 3px rgba(0,0,0,0.8); /* Sombra para legibilidad */
    }
    .metric-label {
        font-size: 10px;
        font-weight: 700;
        color: #e0e0e0;
        text-transform: uppercase;
        margin-top: 2px;
    }
    
    /* Ajuste de imagenes nativas */
    div[data-testid="stImage"] {
        margin-bottom: -5px;
    }
    div[data-testid="stImage"] > img {
        width: 50px !important;
        object-fit: contain;
    }
</style>
""", unsafe_allow_html=True)

# --- RECURSOS ---
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
    base_dir = os.path.dirname(os.path.abspath(__file__))
    paths = [os.path.join(base_dir, "imagenes", filename), os.path.join(base_dir, filename)]
    for p in paths:
        if os.path.exists(p): return p
    return None

def normalizar_linea(texto):
    if not isinstance(texto, str): return str(texto)
    t = texto.strip().title()
    if "Linea" in t and "Línea" not in t: t = t.replace("Linea", "Línea")
    return t

# --- RENDERIZADO INTELIGENTE (CENTRADO) ---
def render_metrics_centered(df):
    if df.empty: return

    # 1. Preparar Datos
    dias = df["fecha"].nunique() or 1
    
    # Lista de items a mostrar: [(Nombre, Valor, Imagen, Color), ...]
    items_to_show = []
    
    # A) Sistema
    val_sys = df["afluencia"].sum() / dias
    items_to_show.append({
        "label": "Sistema Total", "val": val_sys, 
        "img": "ícono-MB.png", "color": "#333", "is_sys": True
    })
    
    # B) Líneas
    df_l = df.groupby("linea")["afluencia"].sum().reset_index()
    df_l["promedio"] = df_l["afluencia"] / dias
    df_l = df_l.sort_values("linea")
    
    for _, row in df_l.iterrows():
        nombre = normalizar_linea(row["linea"])
        items_to_show.append({
            "label": nombre.replace("Línea ", "L"), 
            "val": row["promedio"],
            "img": IMAGENES.get(nombre, "ícono-MB.png"),
            "color": COLOR_MAP.get(nombre, "#555"),
            "is_sys": False
        })

    # 2. Algoritmo de Centrado (Columnas Fantasma)
    # Definimos una rejilla fija de 9 columnas (ancho máximo razonable)
    MAX_COLS = 9 
    n_items = len(items_to_show)
    
    # Calculamos dónde empezar para que queden centrados
    # Ej: Si hay 3 items, start_idx = (9-3)//2 = 3. Ocuparán cols 3, 4, 5.
    start_idx = max(0, (MAX_COLS - n_items) // 2)
    
    # Creamos las columnas físicas
    cols = st.columns(MAX_COLS)
    
    # Llenamos solo las columnas centrales
    for i in range(n_items):
        # Indice real en la rejilla
        grid_col_idx = start_idx + i
        
        # Evitar desbordamiento si hay más de 9 items (raro en este caso)
        if grid_col_idx >= MAX_COLS: break
        
        item = items_to_show[i]
        
        with cols[grid_col_idx]:
            # Imagen
            path = get_img_path(item["img"])
            if path:
                st.image(path, width=50)
            else:
                # Fallback círculo
                st.markdown(f'<div style="background:{item["color"]};width:40px;height:40px;border-radius:50%;margin:0 auto 5px auto;"></div>', unsafe_allow_html=True)
            
            # Texto (Blanco)
            st.markdown(f"""
                <div class="metric-value">{item['val']:,.0f}</div>
                <div class="metric-label">{item['label']}</div>
            """, unsafe_allow_html=True)

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

    # --- SIDEBAR: FILTROS ---
    st.sidebar.header("Filtros")
    min_d, max_d = df["fecha"].min(), df["fecha"].max()
    ini = st.sidebar.date_input("Inicio", min_d)
    fin = st.sidebar.date_input("Fin", max_d)
    st.sidebar.divider()

    # Selector de Casillas (Checkboxes)
    st.sidebar.subheader("Líneas a visualizar")
    all_lines = sorted(df["linea"].unique())
    sel_lines = []
    
    # Contenedor para casillas más compacto
    for linea in all_lines:
        if st.sidebar.checkbox(linea, value=True, key=linea):
            sel_lines.append(linea)
            
    if not sel_lines:
        st.warning("Selecciona al menos una línea.")
        return

    # Aplicar
    mask = (df["fecha"].dt.date >= ini) & (df["fecha"].dt.date <= fin) & (df["linea"].isin(sel_lines))
    df_f = df.loc[mask]

    if df_f.empty:
        st.warning("Sin datos.")
        return

    # --- HEADER CENTRADO ---
    st.markdown("###")
    render_metrics_centered(df_f)
    st.markdown("---")

    # --- GRAFICAS ---
    c1, c2 = st.columns([2, 1])

    with c1:
        st.subheader("Tendencia Diaria")
        df_t = df_f.groupby(["fecha", "linea"])["afluencia"].sum().reset_index()
        fig1 = px.line(df_t, x="fecha", y="afluencia", color="linea", color_discrete_map=COLOR_MAP)
        fig1.update_layout(template="plotly_white", xaxis_title="", yaxis_title="Pasajeros", legend=dict(orientation="h", y=1.1, x=0.5, xanchor="center"))
        st.plotly_chart(fig1, use_container_width=True)

    with c2:
        st.subheader("Distribución")
        df_p = df_f.groupby("linea")["afluencia"].sum().reset_index()
        fig2 = px.pie(df_p, values="afluencia", names="linea", color="linea", color_discrete_map=COLOR_MAP, hole=0.6)
        fig2.update_layout(template="plotly_white", showlegend=False, margin=dict(t=20, b=20, l=20, r=20))
        fig2.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig2, use_container_width=True)

if __name__ == "__main__":
    main()
