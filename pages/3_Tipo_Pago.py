import streamlit as st
import plotly.express as px
from utils import cargar_datos

st.set_page_config(page_title="Tipos de Pago", layout="wide")

st.title("💳 Análisis por Tipo de Acceso")
df = cargar_datos()

# --- KPIs ---
total_viajes = df["afluencia"].sum()
df_tipo = df.groupby("tipo_pago")["afluencia"].sum().reset_index()
df_tipo["porcentaje"] = (df_tipo["afluencia"] / total_viajes) * 100

c1, c2, c3 = st.columns(3)
c1.metric("Total Viajes", f"{total_viajes:,.0f}")

# Mostrar métricas dinámicas para cada tipo encontrado
for i, row in df_tipo.iterrows():
    if i < 2: # Solo mostrar los primeros 2 en tarjetas
        col = c2 if i == 0 else c3
        col.metric(f"{row['tipo_pago']}", f"{row['afluencia']:,.0f}", f"{row['porcentaje']:.1f}% del total")

st.divider()

# --- GRÁFICOS ---
col_g1, col_g2 = st.columns(2)

with col_g1:
    st.subheader("Distribución Global")
    fig_pie = px.pie(df_tipo, values="afluencia", names="tipo_pago", hole=0.4, title="Proporción de Accesos")
    st.plotly_chart(fig_pie, use_container_width=True)

with col_g2:
    st.subheader("Composición por Línea")
    # Gráfico de barras apiladas al 100% para ver la proporción
    df_linea_pago = df.groupby(["linea", "tipo_pago"])["afluencia"].sum().reset_index()
    fig_bar = px.bar(
        df_linea_pago, x="linea", y="afluencia", color="tipo_pago", 
        title="Prepago vs Gratuidad por Línea",
        barmode="group" # O usa "stack" si prefieres apiladas
    )
    st.plotly_chart(fig_bar, use_container_width=True)

st.subheader("Tendencia Temporal por Tipo de Pago")
df_time = df.groupby(["fecha", "tipo_pago"])["afluencia"].sum().reset_index()
fig_area = px.area(df_time, x="fecha", y="afluencia", color="tipo_pago", title="Evolución de Tipos de Acceso")
st.plotly_chart(fig_area, use_container_width=True)
