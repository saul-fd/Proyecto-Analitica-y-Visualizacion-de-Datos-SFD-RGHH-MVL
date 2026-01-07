import streamlit as st
import plotly.express as px
from utils import cargar_datos

st.title("Comportamiento Temporal")

df = cargar_datos()

df_mes = df.groupby(["anio", "mes"])["afluencia"].sum().reset_index()

fig = px.bar(
    df_mes,
    x="mes",
    y="afluencia",
    color="anio",
    barmode="group",
    title="Afluencia mensual por año"
)

st.plotly_chart(fig, use_container_width=True)
