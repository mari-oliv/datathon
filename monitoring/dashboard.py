import streamlit as st
import pandas as pd
import pickle
from pathlib import Path
import plotly.express as px
import sys
import numpy as np


ROOT = Path(__file__).parent.parent.resolve()
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

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

# --- Garantir colunas esperadas pelo modelo ---------------------------------
import re

def _parse_fase_ideal_val(x):
    if pd.isna(x):
        return None
    s = str(x).strip()
    m = re.search(r"\d+", s)
    return float(m.group()) if m else None

# Se o dataset não tiver `Fase_ideal_num`, tenta extrair de `Fase ideal` (quando existir)
if "Fase_ideal_num" not in df.columns and "Fase ideal" in df.columns:
    df["Fase_ideal_num"] = df["Fase ideal"].apply(_parse_fase_ideal_val)

# Se faltar `gap_fase`, calcula a partir de `Fase_ideal_num` e `Fase` quando possível
if "gap_fase" not in df.columns:
    if "Fase_ideal_num" in df.columns and "Fase" in df.columns:
        df["gap_fase"] = df["Fase_ideal_num"] - df["Fase"]
    else:
        # cria coluna vazia para manter compatibilidade
        df["gap_fase"] = pd.NA


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
        mean = np.nan if pd.isna(s.mean()) else float(s.mean())
        std = np.nan if pd.isna(s.std()) else float(s.std())
        missing = float(s.isna().mean())
        model_mu = np.nan
        if i < len(mu) and mu[i] is not None:
            try:
                model_mu = float(mu[i])
            except Exception:
                model_mu = np.nan
        model_sigma = np.nan
        if i < len(sigma) and sigma[i] is not None:
            try:
                model_sigma = float(sigma[i])
            except Exception:
                model_sigma = np.nan
        delta = np.nan if (pd.isna(mean) or pd.isna(model_mu)) else float(mean - model_mu)
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


# cluster distribution
try:
    from src.processing_and_models import predict_kmeans_model

    # garantir que todas as colunas esperadas existam no dataframe
    for col in risk_cols:
        if col not in df.columns:
            df[col] = pd.NA

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
