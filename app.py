import streamlit as st
import pandas as pd
import plotly.express as px
import os
import datetime
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
    /* Centrar contenido dentro de las columnas */
    [data-testid="column"] {
        text-align: center;
        display: flex;
        flex-direction: column;
        align-items: center;
    }
    
    /* Textos Métricas */
    .metric-value {
        font-size: 20px;
        font-weight: 800;
        color: #ffffff;
        margin-top: 5px;
        line-height: 1.2;
        text-shadow: 0px 1px 3px rgba(0,0,0,0.8);
    }
    .metric-label {
        font-size: 10px;
        font-weight: 700;
        color: #e0e0e0;
        text-transform: uppercase;
        margin-top: 2px;
    }
    
    /* Imagenes Nativas */
    div[data-testid="stImage"] { margin-bottom: -5px; }
    div[data-testid="stImage"] > img { width: 50px !important; object-fit: contain; }
</style>
""", unsafe_allow_html=True)

# --- RECURSOS ---
IMAGENES = {
    "Línea 1": "MB-1.png", "Línea 2": "MB-2.png", "Línea 3": "MB-3.png",
    "Línea 4": "MB-4.png", "Línea 5": "MB-5.png", "Línea 6": "MB-6.png",
    "Línea 7": "MB-7.png", "Emergente": "ícono-MB.png"
}

COLOR_MAP = {
    'Línea 1': '#B5261E', 'Línea 2': '#6A1B9A', 'Línea 3': '#7CB342',
    'Línea 4': '#EF6C00', 'Línea 5': '#0288D1', 'Línea 6': '#D81B60',
    'Línea 7': '#2E7D32', 'Emergente': '#616161'
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

# --- RENDERIZADO MÉTRICAS ---
def render_metrics_centered(df):
    if df.empty: return
    dias = df["fecha"].nunique() or 1
    
    # Preparar items
    items = []
    # Sistema
    val_sys = df["afluencia"].sum() / dias
    items.append({"label": "Sistema Total", "val": val_sys, "img": "ícono-MB.png", "color": "#333", "is_sys": True})
    
    # Líneas
    df_l = df.groupby("linea")["afluencia"].sum().reset_index()
    df_l["promedio"] = df_l["afluencia"] / dias
    df_l = df_l.sort_values("linea")
    
    for _, row in df_l.iterrows():
        nombre = normalizar_linea(row["linea"])
        items.append({
            "label": nombre.replace("Línea ", "L"), 
            "val": row["promedio"],
            "img": IMAGENES.get(nombre, "ícono-MB.png"),
            "color": COLOR_MAP.get(nombre, "#555")
        })

    # Renderizado Centrado (Columnas Fantasma)
    MAX_COLS = 9 
    n_items = len(items)
    start_idx = max(0, (MAX_COLS - n_items) // 2)
    cols = st.columns(MAX_COLS)
    
    for i in range(n_items):
        grid_col_idx = start_idx + i
        if grid_col_idx >= MAX_COLS: break
        item = items[i]
        
        with cols[grid_col_idx]:
            path = get_img_path(item["img"])
            if path:
                st.image(path, width=50)
            else:
                st.markdown(f'<div style="background:{item["color"]};width:40px;height:40px;border-radius:50%;margin:0 auto 5px auto;"></div>', unsafe_allow_html=True)
            
            st.markdown(f"""
                <div class="metric-value">{item['val']:,.0f}</div>
                <div class="metric-label">{item['label']}</div>
            """, unsafe_allow_html=True)

# --- APP PRINCIPAL ---
def main():
    # --- BARRA LATERAL: NAVEGACIÓN ---
    st.sidebar.header("Navegación")
    
    # CORRECCIÓN: Eliminamos el enlace a "app.py" aquí para evitar el KeyError
    # Solo mostramos el enlace a las otras páginas
    st.sidebar.page_link("pages/1_Lineas.py", label="🚌 Detalle por Línea", use_container_width=True)
    
    st.sidebar.divider()

    st.title("Tablero General de Afluencia")

    try:
        df = cargar_datos()
    except Exception as e:
        st.error(f"Error cargando datos: {e}")
        return

    if 'linea' in df.columns: df['linea'] = df['linea'].apply(normalizar_linea)

    # --- FILTROS ---
    st.sidebar.header("Filtros")
    
    # 1. Restricción de Fechas
    MIN_FECHA = datetime.date(2021, 1, 1)
    MAX_FECHA = datetime.date(2025, 11, 30)
    
    default_start = max(df["fecha"].min().date(), MIN_FECHA)
    default_end = min(df["fecha"].max().date(), MAX_FECHA)
    
    ini = st.sidebar.date_input("Fecha Inicio", value=default_start, min_value=MIN_FECHA, max_value=MAX_FECHA)
    fin = st.sidebar.date_input("Fecha Fin", value=default_end, min_value=MIN_FECHA, max_value=MAX_FECHA)
    
    st.sidebar.divider()

    # 2. Filtro de Líneas (Checkboxes)
    st.sidebar.subheader("Líneas a visualizar")
    all_lines = sorted(df["linea"].unique())
    sel_lines = []
    for linea in all_lines:
        if st.sidebar.checkbox(linea, value=True, key=linea):
            sel_lines.append(linea)
            
    if not sel_lines:
        st.warning("Selecciona al menos una línea.")
        return

    # APLICAR FILTROS
    mask = (df["fecha"].dt.date >= ini) & (df["fecha"].dt.date <= fin) & (df["linea"].isin(sel_lines))
    df_f = df.loc[mask]

    if df_f.empty:
        st.warning("Sin datos para este rango o selección.")
        return

    # --- SECCIÓN 1: HEADER ---
    st.markdown("###")
    render_metrics_centered(df_f)
    st.markdown("---")

    # --- SECCIÓN 2: GRÁFICAS DE AFLUENCIA ---
    c1, c2 = st.columns([2, 1])
    
    with c1:
        st.subheader("Tendencia de Afluencia")
        df_t = df_f.groupby(["fecha", "linea"])["afluencia"].sum().reset_index()
        fig1 = px.line(df_t, x="fecha", y="afluencia", color="linea", color_discrete_map=COLOR_MAP)
        fig1.update_layout(template="plotly_white", xaxis_title="", yaxis_title="Pasajeros", legend=dict(orientation="h", y=1.1, x=0.5, xanchor="center"))
        st.plotly_chart(fig1, use_container_width=True)

    with c2:
        st.subheader("Distribución por Línea")
        df_p = df_f.groupby("linea")["afluencia"].sum().reset_index()
        fig2 = px.pie(df_p, values="afluencia", names="linea", color="linea", color_discrete_map=COLOR_MAP, hole=0.6)
        fig2.update_layout(template="plotly_white", showlegend=False, margin=dict(t=20, b=20, l=20, r=20))
        fig2.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig2, use_container_width=True)

    # --- SECCIÓN 3: ANÁLISIS DE TIPO DE PAGO ---
    st.markdown("---")
    st.subheader("💳 Análisis por Tipo de Pago")
    
    if "tipo_pago" in df_f.columns:
        col_pago1, col_pago2 = st.columns(2)
        
        with col_pago1:
            st.markdown("**Distribución General de Pagos**")
            df_pago_gral = df_f.groupby("tipo_pago")["afluencia"].sum().reset_index()
            fig_pago_pie = px.pie(
                df_pago_gral, 
                values="afluencia", 
                names="tipo_pago", 
                hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            fig_pago_pie.update_traces(textinfo='percent+label')
            st.plotly_chart(fig_pago_pie, use_container_width=True)
            
        with col_pago2:
            st.markdown("**Tipo de Pago por Línea**")
            df_pago_linea = df_f.groupby(["linea", "tipo_pago"])["afluencia"].sum().reset_index()
            fig_pago_bar = px.bar(
                df_pago_linea, 
                x="linea", 
                y="afluencia", 
                color="tipo_pago",
                title="",
                color_discrete_sequence=px.colors.qualitative.Pastel,
                barmode="stack"
            )
            fig_pago_bar.update_layout(template="plotly_white", xaxis_title="", yaxis_title="Total Viajes")
            st.plotly_chart(fig_pago_bar, use_container_width=True)
    else:
        st.info("La columna 'tipo_pago' no se encontró en los datos cargados.")

if __name__ == "__main__":
    main()
