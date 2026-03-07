import streamlit as st
import pandas as pd
import pickle
from pathlib import Path
import plotly.express as px

st.set_page_config(layout="wide", page_title="Monitoramento - Passos Mágicos")

MODEL_PATH = Path("src") / "model" / "model.pkl"
CSV_PATH = Path("src") / "base_dados_pede_2024_ajustado.csv"

st.title("Dashboard de Monitoramento — Modelo de Risco de Defasagem")

if not MODEL_PATH.exists():
    st.error(f"Modelo não encontrado em {MODEL_PATH}. Rode o treino e gere o model.pkl")
    st.stop()

if not CSV_PATH.exists():
    st.error(f"Dataset não encontrado em {CSV_PATH}.")
    st.stop()

# carrega modelo
with open(MODEL_PATH, "rb") as f:
    model = pickle.load(f)

risk_cols = model.get("risk_cols", [])
mu = model.get("mu", [])
sigma = model.get("sigma", [])
centroids = model.get("centroids", [])

st.sidebar.header("Modelo")
st.sidebar.write(f"k = {model.get('k')}")
st.sidebar.write(f"features = {risk_cols}")

# carrega dados
df = pd.read_csv(CSV_PATH)

st.header("Resumo dos Dados")
col1, col2 = st.columns(2)
with col1:
    st.metric("Linhas no dataset", len(df))
    st.metric("Colunas no dataset", df.shape[1])
with col2:
    st.metric("Modelo k", model.get("k"))

# calcula estatísticas por feature
rows = []
for i, col in enumerate(risk_cols):
    if col in df.columns:
        s = pd.to_numeric(df[col], errors="coerce")
        mean = None if pd.isna(s.mean()) else float(s.mean())
        std = None if pd.isna(s.std()) else float(s.std())
        missing = float(s.isna().mean())
        model_mu = float(mu[i]) if i < len(mu) else None
        model_sigma = float(sigma[i]) if i < len(sigma) else None
        delta = None if mean is None or model_mu is None else mean - model_mu
        rows.append({
            "feature": col,
            "data_mean": mean,
            "data_std": std,
            "missing_rate": missing,
            "model_mu": model_mu,
            "model_sigma": model_sigma,
            "delta_mu": delta,
        })
    else:
        rows.append({"feature": col, "error": "not present in dataset"})

stats_df = pd.DataFrame(rows)

st.subheader("Comparação: média do dataset vs média do treino (mu)")
st.dataframe(stats_df)

# gráfico de delta
if not stats_df['delta_mu'].isna().all():
    fig = px.bar(stats_df.dropna(subset=['delta_mu']), x='feature', y='delta_mu', title='Delta entre média atual e mu (treino)')
    st.plotly_chart(fig, use_container_width=True)

# cluster distribution (se possível)
try:
    from src.processing_and_models import predict_kmeans_model
    X_df_new = df[risk_cols].copy()
    X_df_new = X_df_new.apply(pd.to_numeric, errors='coerce')
    mu_arr = pd.Series(mu, index=risk_cols)
    X_df_new = X_df_new.fillna(mu_arr)
    labels = predict_kmeans_model(X_df_new, model)
    cluster_counts = pd.Series(labels).value_counts().sort_index()
    st.subheader('Distribuição dos clusters (aplicando centroids do modelo)')
    st.bar_chart(cluster_counts)
except Exception as e:
    st.warning('Não foi possível calcular distribuição por cluster: ' + str(e))

st.markdown('---')
st.write('Exponha este dashboard com `streamlit run monitoring/dashboard.py`.')
