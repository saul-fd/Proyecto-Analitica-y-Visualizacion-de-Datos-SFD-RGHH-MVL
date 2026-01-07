import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import os

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="MI Movilidad CDMX",
    page_icon="🚌",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==========================================
# ⚙️ CONFIGURACIÓN DE IMÁGENES Y COLORES
# ==========================================
# EDITA AQUÍ LOS NOMBRES DE TUS ARCHIVOS DE IMAGEN
# Asegúrate de que estén en la misma carpeta o en una subcarpeta (ej. "imagenes/")
DICCIONARIO_IMAGENES = {
    "Línea 1": "MB-1.png",  # Cambia por el nombre real de tu archivo
    "Línea 2": "MB-2.png",
    "Línea 3": "MB-3.png",
    "Línea 4": "MB-4.png",
    "Línea 5": "MB-5.png",
    "Línea 6": "MB-6.png",
    "Línea 7": "MB-7.png",
    "Emergente": "MB-Emergente.png"
}

# Colores oficiales del Metrobús para gráficas y fallbacks
COLOR_MAP = {
    'Línea 1': '#B71C1C', # Rojo
    'Línea 2': '#4A148C', # Morado
    'Línea 3': '#558B2F', # Verde Oliva
    'Línea 4': '#E65100', # Naranja
    'Línea 5': '#0277BD', # Azul
    'Línea 6': '#EC407A', # Rosa
    'Línea 7': '#2E7D32', # Verde
    'Emergente': '#616161' # Gris
}

# --- ESTILOS CSS (REPLICA VISUAL HTML) ---
st.markdown("""
<style>
    /* Contenedor principal limpio */
    .main .block-container {
        padding-top: 2rem;
        max-width: 95%;
    }
    
    /* Tarjetas KPI Superiores */
    .kpi-card {
        background-color: white;
        border-radius: 8px;
        padding: 20px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05);
        text-align: center;
        border-bottom: 4px solid #00b894; /* Verde institucional */
        margin-bottom: 20px;
    }
    .kpi-value {
        font-size: 28px;
        font-weight: 800;
        color: #2d3436;
        margin: 5px 0;
    }
    .kpi-label {
        font-size: 14px;
        color: #636e72;
        text-transform: uppercase;
        font-weight: 600;
    }
    
    /* Estilos para los iconos de las líneas */
    .line-icon-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        margin-bottom: 10px;
    }
    .line-badge {
        width: 60px;
        height: 60px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-weight: bold;
        font-size: 24px;
        box-shadow: 0 3px 6px rgba(0,0,0,0.2);
    }
    .line-name {
        font-size: 12px;
        color: #636e72;
        margin-top: 5px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# --- FUNCIÓN DE CARGA ---
@st.cache_data
def cargar_datos():
    archivo = "afluencia-mb-2025.csv"
    if not os.path.exists(archivo):
        return None, f"No se encontró el archivo: {archivo}"
    
    try:
        df = pd.read_csv(archivo)
        df.columns = [c.lower().strip() for c in df.columns]
        
        # Procesamiento de Fechas
        col_fecha = next((c for c in df.columns if 'fecha' in c), None)
        if col_fecha:
            df[col_fecha] = pd.to_datetime(df[col_fecha])
            # Crear columnas auxiliares para gráficas
            df['Mes'] = df[col_fecha].dt.month_name(locale='es_ES') if hasattr(df[col_fecha].dt, 'month_name') else df[col_fecha].dt.month
            df['Mes_Num'] = df[col_fecha].dt.month
        
        return df, None
    except Exception as e:
        return None, str(e)

# --- COMPONENTES VISUALES ---

def mostrar_encabezado_lineas():
    """Renderiza el carrusel de iconos de líneas en la parte superior"""
    st.markdown("###") 
    cols = st.columns(len(DICCIONARIO_IMAGENES))
    
    for i, (nombre_linea, nombre_archivo) in enumerate(DICCIONARIO_IMAGENES.items()):
        if i >= len(cols): break # Evitar desbordamiento
        
        with cols[i]:
            # Verificar si existe imagen en carpeta raiz o 'imagenes/'
            rutas_posibles = [nombre_archivo, os.path.join("imagenes", nombre_archivo)]
            imagen_encontrada = None
            for ruta in rutas_posibles:
                if os.path.exists(ruta):
                    imagen_encontrada = ruta
                    break
            
            if imagen_encontrada:
                st.image(imagen_encontrada, width=70, output_format="PNG")
            else:
                # Fallback: Círculo de color si no hay imagen
                color = COLOR_MAP.get(nombre_linea, "#333")
                numero = nombre_linea.replace("Línea ", "").replace("Emergente", "E")
                st.markdown(f"""
                    <div class="line-icon-container">
                        <div class="line-badge" style="background-color: {color};">
                            {numero}
                        </div>
                        <div class="line-name">{nombre_linea}</div>
                    </div>
                """, unsafe_allow_html=True)
    st.markdown("---")

def mostrar_kpi(col, titulo, valor, icono):
    col.markdown(f"""
        <div class="kpi-card">
            <div style="font-size:24px;">{icono}</div>
            <div class="kpi-value">{valor}</div>
            <div class="kpi-label">{titulo}</div>
        </div>
    """, unsafe_allow_html=True)

# ==========================================
# 🚀 EJECUCIÓN PRINCIPAL
# ==========================================

df, error = cargar_datos()

if df is not None:
    # 1. MOSTRAR ICONOS DE LÍNEAS
    mostrar_encabezado_lineas()
    
    st.markdown("<h2 style='text-align: center; color: #2d3436; margin-bottom: 30px;'>Tablero de Control - Afluencia Metrobús</h2>", unsafe_allow_html=True)

    # Detección de columnas
    col_linea = next((c for c in df.columns if c in ['linea', 'línea', 'corredor']), df.columns[0])
    col_afluencia = next((c for c in df.select_dtypes(include=np.number).columns if 'afluencia' in c or 'total' in c), df.columns[-1])
    col_fecha = next((c for c in df.columns if 'fecha' in c), None)

    # 2. FILTROS (Sidebar colapsado o Top Bar)
    c1, c2 = st.columns([3, 1])
    with c2:
        lista_lineas = ["Todas"] + sorted(df[col_linea].unique().tolist())
        filtro_linea = st.selectbox("📍 Filtrar por Línea", lista_lineas)
    
    # Aplicar Filtro
    df_filtrado = df.copy()
    if filtro_linea != "Todas":
        df_filtrado = df_filtrado[df_filtrado[col_linea] == filtro_linea]

    # 3. TARJETAS KPI (ESTILO HTML)
    k1, k2, k3, k4 = st.columns(4)
    
    total = df_filtrado[col_afluencia].sum()
    promedio = df_filtrado[col_afluencia].mean()
    maximo = df_filtrado[col_afluencia].max()
    registros = len(df_filtrado)
    
    mostrar_kpi(k1, "Viajes Totales", f"{total:,.0f}", "🚌")
    mostrar_kpi(k2, "Promedio Diario", f"{promedio:,.0f}", "📊")
    mostrar_kpi(k3, "Pico Máximo", f"{maximo:,.0f}", "🏆")
    mostrar_kpi(k4, "Días Analizados", f"{registros}", "📅")

    # 4. GRÁFICOS DETALLADOS
    
    # Gráfico A: Barras Horizontales (Top Líneas) - Solo visible si no filtramos
    if filtro_linea == "Todas":
        st.subheader("📊 Viajes Totales por Línea")
        df_agrupado = df_filtrado.groupby(col_linea)[col_afluencia].sum().reset_index().sort_values(col_afluencia, ascending=True)
        # Asignar colores
        colores = [COLOR_MAP.get(l, '#95a5a6') for l in df_agrupado[col_linea]]
        
        fig_bar = px.bar(df_agrupado, x=col_afluencia, y=col_linea, orientation='h', text_auto='.3s')
        fig_bar.update_layout(template="plotly_white", height=400, xaxis_title="Total de Viajes", yaxis_title="")
        fig_bar.update_traces(marker_color=colores, textfont_size=12)
        st.plotly_chart(fig_bar, use_container_width=True)
    
    # Gráficos B y C: Evolución y Mensual
    row2_c1, row2_c2 = st.columns([2, 1])
    
    with row2_c1:
        st.subheader("📈 Tendencia Diaria")
        if col_fecha:
            df_tiempo = df_filtrado.groupby(col_fecha)[col_afluencia].sum().reset_index()
            # Color dinámico
            color_linea = COLOR_MAP.get(filtro_linea, "#2d3436") if filtro_linea != "Todas" else "#0984e3"
            
            fig_line = px.area(df_tiempo, x=col_fecha, y=col_afluencia)
            fig_line.update_layout(template="plotly_white", height=350, margin=dict(t=20, b=20, l=20, r=20))
            fig_line.update_traces(line_color=color_linea, fillcolor=color_linea)
            st.plotly_chart(fig_line, use_container_width=True)
        else:
            st.warning("No hay columna de fecha para mostrar tendencia.")
            
    with row2_c2:
        st.subheader("📅 Comportamiento Mensual")
        if 'Mes' in df_filtrado.columns:
            df_mes = df_filtrado.groupby(['Mes_Num', 'Mes'])[col_afluencia].sum().reset_index().sort_values('Mes_Num')
            
            fig_mes = px.bar(df_mes, x='Mes', y=col_afluencia)
            fig_mes.update_layout(template="plotly_white", height=350, margin=dict(t=20, b=20, l=20, r=20))
            fig_mes.update_traces(marker_color="#00b894")
            st.plotly_chart(fig_mes, use_container_width=True)

else:
    # Pantalla de Error / Carga inicial
    st.error("⚠️ Archivo de datos no encontrado.")
    st.info(f"Por favor coloca el archivo CSV en la carpeta del proyecto. {error if error else ''}")
