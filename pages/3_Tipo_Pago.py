import streamlit as st
import plotly.express as px
from utils import cargar_datos

st.title("Tipo de Pago")

df = cargar_datos()

fig = px.pie(
    df.groupby("tipo_pago")["afluencia"].sum().reset_index(),
    names="tipo_pago",
    values="afluencia",
    title="Distribución por tipo de pago"
)

st.plotly_chart(fig, use_container_width=True)
