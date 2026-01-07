import streamlit as st
import plotly.express as px
from utils import cargar_datos

st.title("Análisis por Línea")

df = cargar_datos()

lineas = sorted(df["linea"].unique())
linea_sel = st.selectbox("Selecciona una línea", lineas)

df_l = df[df["linea"] == linea_sel]

fig = px.line(
    df_l.groupby("fecha")["afluencia"].sum().reset_index(),
    x="fecha",
    y="afluencia",
    title=f"Evolución diaria - {linea_sel}"
)

st.plotly_chart(fig, use_container_width=True)
