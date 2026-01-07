import streamlit as st
import pandas as pd
import plotly.express as px
import os
import datetime
from utils import cargar_datos

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

def get_img_path(filename):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(current_dir)
    paths = [
        os.path.join(root_dir, "imagenes", filename),
        os.path.join(root_dir, filename)
    ]
    for p in paths:
        if os.path.exists(p): return p
    return None

def normalizar_linea(texto):
    if not isinstance(texto, str): return str(texto)
    t = texto.strip().title()
    if "Linea" in t and "Línea" not in t: t = t.replace("Linea", "Línea")
    return t

def render_line_metrics(df, linea_sel):
    dias = df["fecha"].nunique() or 1
    total = df["afluencia"].sum()
    promedio = total / dias
    maximo = df["afluencia"].max()
    
    nombre_norm = normalizar_linea(linea_sel)
    img_file = IMAGENES.get(nombre_norm, "ícono-MB.png")
    path = get_img_path(img_file)
    
    c_img, c_kpi1, c_kpi2, c_kpi3 = st.columns([1, 1, 1, 1])
    
    with c_img:
        if path: st.image(path, width=70)
        else: st.markdown(f"**{linea_sel}**")
        
    with c_kpi1:
        st.markdown(f'<div class="metric-value">{total:,.0f}</div><div class="metric-label">Viajes Totales</div>', unsafe_allow_html=True)
    with c_kpi2:
        st.markdown(f'<div class="metric-value">{promedio:,.0f}</div><div class="metric-label">Promedio Diario</div>', unsafe_allow_html=True)
    with c_kpi3:
        st.markdown(f'<div class="metric-value">{maximo:,.0f}</div><div class="metric-label">Pico Máximo</div>', unsafe_allow_html=True)

# --- FUNCIÓN PRINCIPAL DE LA VISTA ---
def show_lineas():
    # Estilos CSS
    st.markdown("""
    <style>
        [data-testid="column"] { text-align: center; display: flex; flex-direction: column; align-items: center; }
        .metric-value { font-size: 26px; font-weight: 800; color: #ffffff; margin-top: 5px; text-shadow: 0px 2px 4px rgba(0,0,0,0.8); }
        .metric-label { font-size: 12px; font-weight: 700; color: #e0e0e0; text-transform: uppercase; margin-top: 2px; }
    </style>
    """, unsafe_allow_html=True)

    st.title("Análisis Detallado por Línea")

    try:
        df = cargar_datos()
    except Exception as e:
        st.error(f"Error cargando datos: {e}")
        return

    if 'linea' in df.columns: df['linea'] = df['linea'].apply(normalizar_linea)

    # --- FILTROS ---
    st.sidebar.header("Configuración")
    
    lineas = sorted(df["linea"].unique())
    linea_sel = st.sidebar.selectbox("Selecciona una Línea", lineas)
    
    MIN_FECHA, MAX_FECHA = datetime.date(2021, 1, 1), datetime.date(2025, 11, 30)
    # Ajustamos fechas por defecto para que no salga vacío si el CSV tiene fechas recientes
    min_csv = df["fecha"].min().date()
    max_csv = df["fecha"].max().date()
    
    ini = st.sidebar.date_input("Inicio", min_csv, min_value=MIN_FECHA, max_value=MAX_FECHA)
    fin = st.sidebar.date_input("Fin", max_csv, min_value=MIN_FECHA, max_value=MAX_FECHA)
    
    mask = (df["linea"] == linea_sel) & (df["fecha"].dt.date >= ini) & (df["fecha"].dt.date <= fin)
    df_linea = df.loc[mask]

    if df_linea.empty:
        st.warning(f"No hay datos para {linea_sel} en las fechas seleccionadas.")
        return

    # --- CONTENIDO ---
    st.markdown("###")
    render_line_metrics(df_linea, linea_sel)
    st.markdown("---")

    color_linea = COLOR_MAP.get(normalizar_linea(linea_sel), "#333")

    # 1. EVOLUCIÓN TEMPORAL
    st.subheader("Evolución de Afluencia")
    fig_time = px.area(df_linea.groupby("fecha")["afluencia"].sum().reset_index(), x="fecha", y="afluencia")
    fig_time.update_traces(line_color=color_linea, fillcolor=color_linea)
    st.plotly_chart(fig_time, use_container_width=True)

    # 2. DISPERSIÓN (NUEVO BLOQUE CON BOXPLOT)
    st.markdown("---")
    st.subheader("Dispersión y Variabilidad")
    
    # Preparamos datos para el boxplot (Día de la semana)
    df_box = df_linea.copy()
    df_box["dia_num"] = df_box["fecha"].dt.dayofweek
    dias_map = {0:"Lunes", 1:"Martes", 2:"Miércoles", 3:"Jueves", 4:"Viernes", 5:"Sábado", 6:"Domingo"}
    df_box["dia_semana"] = df_box["dia_num"].map(dias_map)
    df_box = df_box.sort_values("dia_num")

    col_box1, col_box2 = st.columns([3, 1])

    with col_box1:
        st.markdown("**Variabilidad por Día de la Semana**")
        fig_box = px.box(
            df_box, 
            x="dia_semana", 
            y="afluencia", 
            color="dia_semana",
            color_discrete_sequence=px.colors.qualitative.Pastel,
            points="outliers" # Muestra solo los puntos atípicos
        )
        fig_box.update_layout(template="plotly_white", xaxis_title="", yaxis_title="Afluencia", showlegend=False)
        st.plotly_chart(fig_box, use_container_width=True)

    with col_box2:
        st.markdown("**Dispersión Total**")
        fig_box_total = px.box(
            df_box, 
            y="afluencia",
            points="all", # Muestra todos los puntos para ver la densidad
            color_discrete_sequence=[color_linea]
        )
        fig_box_total.update_layout(template="plotly_white", xaxis_title="Periodo", yaxis_title="", showlegend=False)
        st.plotly_chart(fig_box_total, use_container_width=True)

    # 3. TIPO DE PAGO
    if "tipo_pago" in df_linea.columns:
        st.markdown("---")
        st.subheader("Desglose por Tipo de Pago")
        c1, c2 = st.columns(2)
        with c1:
            df_pay = df_linea.groupby("tipo_pago")["afluencia"].sum().reset_index()
            fig_pie = px.pie(df_pay, values="afluencia", names="tipo_pago", hole=0.5, color_discrete_sequence=px.colors.qualitative.Pastel)
            st.plotly_chart(fig_pie, use_container_width=True)
        with c2:
            df_pay_time = df_linea.groupby(["fecha", "tipo_pago"])["afluencia"].sum().reset_index()
            fig_bar = px.bar(df_pay_time, x="fecha", y="afluencia", color="tipo_pago", barmode="stack", color_discrete_sequence=px.colors.qualitative.Pastel)
            st.plotly_chart(fig_bar, use_container_width=True)
