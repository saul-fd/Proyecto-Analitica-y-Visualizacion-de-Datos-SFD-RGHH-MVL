import streamlit as st
import pandas as pd
import plotly.express as px
from utils import cargar_datos

# --- CONFIGURACION DE PAGINA ---
st.set_page_config(
    page_title="Tablero Metrobus CDMX",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- ESTILOS CSS (Sin Emojis, Estilo Corporativo) ---
st.markdown("""
<style>
    .metric-card {
        background-color: #ffffff;
        border-left: 5px solid #ccc;
        border-radius: 5px;
        padding: 15px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        text-align: center;
        margin-bottom: 10px;
    }
    .metric-title {
        font-size: 12px;
        font-weight: bold;
        color: #7f8c8d;
        text-transform: uppercase;
        margin-bottom: 5px;
    }
    .metric-value {
        font-size: 22px;
        font-weight: 800;
        color: #2c3e50;
    }
    .metric-sub {
        font-size: 10px;
        color: #95a5a6;
    }
</style>
""", unsafe_allow_html=True)

# --- CONFIGURACION DE COLORES ---
# Mapa base para lineas conocidas (se usara fallback para nuevas)
COLOR_MAP = {
    'Línea 1': '#B71C1C', 
    'Línea 2': '#4A148C', 
    'Línea 3': '#558B2F', 
    'Línea 4': '#E65100', 
    'Línea 5': '#0277BD', 
    'Línea 6': '#EC407A', 
    'Línea 7': '#2E7D32', 
    'Emergente': '#616161'
}

# --- FUNCION: TARJETAS DE PROMEDIO (DINAMICO) ---
def render_top_metrics(df_filtered):
    """
    Genera dinamicamente una tarjeta por cada linea presente en el dataframe
    mas una tarjeta de resumen general.
    """
    # 1. Calculos Generales
    total_dias = df_filtered["fecha"].nunique()
    if total_dias == 0: total_dias = 1
    
    suma_total = df_filtered["afluencia"].sum()
    promedio_sistema = suma_total / total_dias
    
    # 2. Calculos por Linea
    # Agrupamos por Linea y sumamos toda su afluencia, luego dividimos por dias unicos
    df_lineas = df_filtered.groupby("linea")["afluencia"].sum().reset_index()
    df_lineas["promedio"] = df_lineas["afluencia"] / total_dias
    df_lineas = df_lineas.sort_values("linea")
    
    # 3. Renderizado
    # Columnas: 1 (Sistema) + N (Lineas)
    cols = st.columns(len(df_lineas) + 1)
    
    # A) Tarjeta Sistema
    with cols[0]:
        st.markdown(f"""
        <div class="metric-card" style="border-left-color: #2c3e50;">
            <div class="metric-title">Sistema Total</div>
            <div class="metric-value">{promedio_sistema:,.0f}</div>
            <div class="metric-sub">Promedio Diario</div>
        </div>
        """, unsafe_allow_html=True)
        
    # B) Tarjetas por Linea (Iterativo)
    for idx, row in df_lineas.iterrows():
        nombre_linea = row["linea"]
        valor = row["promedio"]
        
        # Obtener color o usar gris por defecto
        color = COLOR_MAP.get(nombre_linea, "#95a5a6")
        # Acortar nombre para UI (ej. "Linea 1" -> "L1")
        nombre_corto = nombre_linea.replace("Línea ", "L").replace("Emergente", "E")
        
        # Ajustar indice + 1 porque el 0 es el Sistema
        with cols[idx + 1]:
            st.markdown(f"""
            <div class="metric-card" style="border-left-color: {color};">
                <div class="metric-title" style="color:{color};">{nombre_corto}</div>
                <div class="metric-value">{valor:,.0f}</div>
                <div class="metric-sub">Pasajeros/Dia</div>
            </div>
            """, unsafe_allow_html=True)

# --- MAIN ---
def main():
    st.title("Tablero General de Afluencia")
    
    try:
        df = cargar_datos()
    except Exception as e:
        st.error(f"Error al cargar datos: {e}")
        return

    # --- SIDEBAR: FILTROS GLOBALES ---
    st.sidebar.header("Filtros")
    
    # Filtro de Fechas
    min_date = df["fecha"].min()
    max_date = df["fecha"].max()
    
    start_date = st.sidebar.date_input("Fecha Inicio", min_date)
    end_date = st.sidebar.date_input("Fecha Fin", max_date)
    
    # Aplicar Filtros
    mask = (df["fecha"].dt.date >= start_date) & (df["fecha"].dt.date <= end_date)
    df_filtered = df.loc[mask]

    if df_filtered.empty:
        st.warning("No hay datos para el rango de fechas seleccionado.")
        return

    # --- SECCION 1: METRICAS SUPERIORES (KPIs) ---
    render_top_metrics(df_filtered)
    
    st.markdown("---")

    # --- SECCION 2: GRAFICAS PRINCIPALES ---
    col_izq, col_der = st.columns([2, 1])

    with col_izq:
        st.subheader("Evolucion Temporal Comparativa")
        # Grafico de Lineas Multiserie
        # Agrupamos por fecha y linea
        df_chart_time = df_filtered.groupby(["fecha", "linea"])["afluencia"].sum().reset_index()
        
        fig_line = px.line(
            df_chart_time,
            x="fecha",
            y="afluencia",
            color="linea",
            color_discrete_map=COLOR_MAP,
            title="Tendencia Diaria por Linea"
        )
        fig_line.update_layout(
            template="plotly_white",
            xaxis_title="Fecha",
            yaxis_title="Afluencia",
            legend_title="Linea",
            hovermode="x unified",
            height=400
        )
        st.plotly_chart(fig_line, use_container_width=True)

    with col_der:
        st.subheader("Distribucion del Periodo")
        # Grafico de Pastel (Donut)
        df_pie = df_filtered.groupby("linea")["afluencia"].sum().reset_index()
        
        fig_pie = px.pie(
            df_pie,
            values="afluencia",
            names="linea",
            color="linea",
            color_discrete_map=COLOR_MAP,
            hole=0.4,
            title="Participacion Total"
        )
        fig_pie.update_layout(
            template="plotly_white",
            height=400,
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
        )
        fig_pie.update_traces(textposition='inside', textinfo='percent')
        st.plotly_chart(fig_pie, use_container_width=True)

if __name__ == "__main__":
    main()
