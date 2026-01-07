import pandas as pd
import streamlit as st

@st.cache_data
def cargar_datos():
    df = pd.read_csv("data/afluencia-mb-2025.csv")
    df["fecha"] = pd.to_datetime(df["fecha"])
    return df
