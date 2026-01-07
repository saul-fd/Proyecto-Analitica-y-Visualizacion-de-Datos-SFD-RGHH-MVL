import streamlit as st
import plotly.express as px
from utils import cargar_datos

st.set_page_config(
    page_title="MI Movilidad CDMX",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("Tablero General de Afluencia Metrobús")

df = cargar_datos()

total = df["afluencia"].sum()
promedio = df.groupby("fecha")["afluencia"].sum().mean()
maximo = df["afluencia"].max()
registros = len(df)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Viajes totales", f"{total:,.0f}")
c2.metric("Promedio diario", f"{promedio:,.0f}")
c3.metric("Pico máximo", f"{maximo:,.0f}")
c4.metric("Registros", registros)

st.divider()

df_lineas = df.groupby("linea")["afluencia"].sum().reset_index()

fig = px.bar(
    df_lineas,
    x="afluencia",
    y="linea",
    orientation="h",
    title="Viajes totales por línea"
)

st.plotly_chart(fig, use_container_width=True)
