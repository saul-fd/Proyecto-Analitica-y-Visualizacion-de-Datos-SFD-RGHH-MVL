import streamlit as st
import pandas as pd
import plotly.express as px
import os
import datetime
from utils import cargar_datos

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Detalle por Línea - Metrobús",
    page_icon="🚌",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- ESTILOS CSS (Mismo estilo que app.py) ---
st.markdown("""
<style>
    /* Centrado de columnas */
    [data-testid="column"] {
        text-align: center;
        display: flex;
        flex-direction: column;
        align-items: center;
    }
    /* Métricas */
    .metric-value {
        font-size: 26px;
        font-weight: 800;
        color: #ffffff; /* Blanco */
        margin-top: 5px;
        line-height: 1.2;
        text-shadow: 0px 2px 4px rgba(0,0,0,0.8);
    }
    .metric-label {
        font-size: 12px;
        font-weight: 700;
        color: #e0e0e0;
        text-transform: uppercase;
        margin-top: 2px;
    }
    /* Ajuste imágenes */
    div[data-testid="stImage"] { margin-bottom: -5px; }
    div[data-testid="stImage"] > img { width: 60px !important; object-fit: contain; }
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

# --- FUNCIONES AUXILIARES (Replicadas para evitar errores de import) ---
def get_img_path(filename):
    # Buscamos en la carpeta padre 'imagenes' ya que estamos dentro de 'pages/'
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    paths = [os.path.join(base_dir, "imagenes", filename), os.path.join(base_dir, filename)]
    for p in paths:
        if os.path.exists(p): return p
    return None

def normalizar_linea(texto):
    if not isinstance(texto, str): return str(texto)
    t = texto.strip().title()
    if "Linea" in t and "Línea" not in t: t = t.replace("Linea", "Línea")
    return t

# --- RENDERIZADO DE TARJETAS ---
def render_line_metrics(df, linea_sel):
    dias = df["fecha"].nunique() or 1
    total = df["afluencia"].sum()
    promedio = total / dias
    maximo = df["afluencia"].max()
    
    # Obtener recursos visuales
    nombre_norm = normalizar_linea(linea_sel)
    img_file = IMAGENES.get(nombre_norm, "ícono-MB.png")
    color = COLOR_MAP.get(nombre_norm, "#555")
    path = get_img_path(img_file)
    
    # Renderizado Centrado
    c_img, c_kpi1, c_kpi2, c_kpi3 = st.columns([1, 1, 1, 1])
    
    with c_img:
        if path: st.image(path, width=70)
        else: st.markdown(f"**{linea_sel}**")
        
    with c_kpi1:
        st.markdown(f"""
            <div class="metric-value">{total:,.0f}</div>
            <div class="metric-label">Viajes Totales (Periodo)</div>
        """, unsafe_allow_html=True)
        
    with c_kpi2:
        st.markdown(f"""
            <div class="metric-value">{promedio:,.0f}</div>
            <div class="metric-label">Promedio Diario</div>
        """, unsafe_allow_html=True)

    with c_kpi3:
        st.markdown(f"""
            <div class="metric-value">{maximo:,.0f}</div>
            <div class="metric-label">Pico Máximo</div>
        """, unsafe_allow_html=True)

# --- APP PRINCIPAL ---
def main():
    # --- SIDEBAR NAVEGACIÓN ---
    st.sidebar.header("Navegación")
    st.sidebar.page_link("app.py", label="🏠 Inicio (General)", use_container_width=True)
    st.sidebar.page_link("pages/1_Lineas.py", label="🚌 Detalle por Línea", use_container_width=True)
    st.sidebar.divider()

    st.title("Análisis Detallado por Línea")

    try:
        df = cargar_datos()
    except Exception as e:
        st.error(f"Error cargando datos: {e}")
        return

    if 'linea' in df.columns: df['linea'] = df['linea'].apply(normalizar_linea)

    # --- FILTROS ---
    st.sidebar.header("Configuración")
    
    # 1. Selector de Línea Única
    lineas = sorted(df["linea"].unique())
    linea_sel = st.sidebar.selectbox("Selecciona una Línea", lineas)
    
    # 2. Filtro de Fecha
    min_f, max_f = df["fecha"].min().date(), df["fecha"].max().date()
    ini = st.sidebar.date_input("Inicio", min_f, min_value=datetime.date(2021,1,1), max_value=datetime.date(2025,11,30))
    fin = st.sidebar.date_input("Fin", max_f, min_value=datetime.date(2021,1,1), max_value=datetime.date(2025,11,30))
    
    # Filtrar
    mask = (df["linea"] == linea_sel) & (df["fecha"].dt.date >= ini) & (df["fecha"].dt.date <= fin)
    df_linea = df.loc[mask]

    if df_linea.empty:
        st.warning(f"No hay datos para {linea_sel} en las fechas seleccionadas.")
        return

    # --- HEADER ---
    st.markdown("###")
    render_line_metrics(df_linea, linea_sel)
    st.markdown("---")

    # --- GRÁFICAS ---
    # Color específico de la línea
    color_linea = COLOR_MAP.get(normalizar_linea(linea_sel), "#333")

    # 1. Evolución Temporal
    st.subheader("Evolución de Afluencia")
    fig_time = px.area(
        df_linea.groupby("fecha")["afluencia"].sum().reset_index(),
        x="fecha", y="afluencia",
        title=""
    )
    fig_time.update_traces(line_color=color_linea, fillcolor=color_linea)
    fig_time.update_layout(template="plotly_white", xaxis_title="", yaxis_title="Pasajeros")
    st.plotly_chart(fig_time, use_container_width=True)

    # 2. Análisis de Pagos (Si existe)
    if "tipo_pago" in df_linea.columns:
        st.subheader("Desglose por Tipo de Pago")
        c1, c2 = st.columns(2)
        
        with c1:
            # Pastel
            df_pay = df_linea.groupby("tipo_pago")["afluencia"].sum().reset_index()
            fig_pie = px.pie(df_pay, values="afluencia", names="tipo_pago", hole=0.5, color_discrete_sequence=px.colors.qualitative.Pastel)
            fig_pie.update_traces(textinfo='percent+label')
            st.plotly_chart(fig_pie, use_container_width=True)
            
        with c2:
            # Evolución de Pagos
            df_pay_time = df_linea.groupby(["fecha", "tipo_pago"])["afluencia"].sum().reset_index()
            fig_bar = px.bar(df_pay_time, x="fecha", y="afluencia", color="tipo_pago", color_discrete_sequence=px.colors.qualitative.Pastel)
            fig_bar.update_layout(template="plotly_white", xaxis_title="", barmode="stack")
            st.plotly_chart(fig_bar, use_container_width=True)

if __name__ == "__main__":
    main()
