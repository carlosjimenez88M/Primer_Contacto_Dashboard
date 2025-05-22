import streamlit as st
import pandas as pd
import plotly.express as px
import seaborn as sns
import matplotlib.pyplot as plt
import openai
import os
from dotenv import load_dotenv


load_dotenv()


openai.api_key = os.getenv("OPENAI_API_KEY")

st.set_page_config(page_title="Primer contacto Inmobiliario Medellín", layout="wide")


import boto3
from io import BytesIO

def cargar_csv_desde_s3(nombre_archivo_s3):
    s3 = boto3.client(
        "s3",
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        region_name=os.getenv("AWS_REGION")
    )
    obj = s3.get_object(Bucket=os.getenv("AWS_BUCKET_NAME"), Key=nombre_archivo_s3)
    df = pd.read_csv(BytesIO(obj['Body'].read()))
    return df


df = cargar_csv_desde_s3("processed/2025-05-22_08-21_propiedades_medellin_completo.csv")



pages = {
    "🏠 Análisis de Datos": "analisis",
    "📘 Información de Primer Contacto": "info"
}
page = st.sidebar.radio("Navegación", list(pages.keys()))

if pages[page] == "analisis":
    st.title("🏠 Primer contacto Inmobiliario Medellín")
    st.markdown("Análisis de propiedades por zona, precio, área y más.")

    zona = st.selectbox("Selecciona una zona base", sorted(df["zona_base"].dropna().unique()))
    df_filtrado = df[df["zona_base"] == zona]

    col1, col2 = st.columns(2)
    col1.metric("Propiedades listadas", df_filtrado.shape[0])
    col2.metric("Precio promedio", f"{int(df_filtrado['precio'].median()):,} COP".replace(",", "."))

    st.subheader("Relación entre precio y área")
    fig = px.scatter(df_filtrado, x="area_m2", y="precio", color="subzona",
                     size="habitaciones", hover_data=["titulo", "link"],
                     labels={"area_m2": "Área (m²)", "precio": "Precio (COP)"})
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("📈 Matriz de correlaciones")
    df["precio_m2"] = df["precio"] / df["area_m2"]
    corr = df[["precio", "area_m2", "precio_m2", "habitaciones", "baños", "parqueaderos"]].corr()
    st.dataframe(corr.round(2))

    st.subheader("📦 Distribución de precios por subzona")
    fig_box = px.box(df_filtrado, x="subzona", y="precio", points="all")
    st.plotly_chart(fig_box, use_container_width=True)

    st.subheader("🤖 Análisis resumido con IA")
    zona_summary = df.groupby("zona_base").agg(
        cantidad_propiedades=("zona_base", "count"),
        precio_promedio=("precio", "mean"),
        area_promedio=("area_m2", "mean"),
        precio_m2_promedio=("precio_m2", "mean"),
        habitaciones_promedio=("habitaciones", "mean"),
        banos_promedio=("baños", "mean"),
        parqueaderos_promedio=("parqueaderos", "mean")
    ).sort_values(by="precio_m2_promedio", ascending=False).round(0).head(15)

    def resumen_llm_resumido(df_summary):
        resumen = df_summary.to_markdown()
        prompt = f"""
Eres un analista de datos inmobiliarios. Analiza el siguiente resumen por zona base en Medellín:

{resumen}

Haz un análisis de máximo 10 líneas que incluya:
- Zonas más caras y baratas por metro cuadrado
- Zonas con más área promedio
- Zonas con más habitaciones o parqueaderos
- Cualquier curiosidad estadística relevante
- dame todo en bullet points
"""
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )
        return response.choices[0].message["content"]

    if st.button("📊 Generar análisis con IA"):
        resumen = resumen_llm_resumido(zona_summary)
        st.markdown(resumen)

elif pages[page] == "info":
    st.title("📘 Información de Primer Contacto")
    st.info("Esta sección estará disponible próximamente.")