#Espelha o pipeline usado no notebook processing.ipynb.


from __future__ import annotations

import logging
import re

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# Pesos do score de risco, baseados na importância de cada indicador.
RISK_WEIGHTS = {
    "defasagem_risco": 0.35,
    "neg_ida": 0.30,
    "neg_ieg": 0.20,
    "neg_ipv": 0.15,
}


def _parse_fase_ideal(x) -> float | None:
    """Extrai número de strings. Ex: 'Fase 8 (Universitários)'."""
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return None
    m = re.search(r"\d+", str(x).strip())
    return float(m.group()) if m else None


def _normalize_bool(value: str | None) -> bool:
    """Converte 'Sim'/'Não' para bool."""
    if value is None:
        return False
    return str(value).strip().lower() in {"sim", "s", "true", "1", "yes", "y"}


def preprocess(student_data: dict, model: dict) -> tuple[np.ndarray, float, float | None]:
    """
    Transforma um dicionário de dados de aluno em feature vector padronizado.

    Retorna:
        X_scaled: array (1, n_features)
        risk_score: float
        gap_fase: float | None
    """
    risk_cols: list[str] = model["risk_cols"]
    mu = np.array(model["mu"])
    sigma = np.array(model["sigma"])

    #features
    fase = student_data.get("Fase")
    fase_ideal_raw = student_data.get("Fase ideal")
    fase_ideal_num = _parse_fase_ideal(fase_ideal_raw)

    gap_fase: float | None = None
    if fase is not None and fase_ideal_num is not None:
        gap_fase = fase_ideal_num - float(fase)

    pv_bool = _normalize_bool(student_data.get("Atingiu Ponto de Virada"))

    #monta linha do DataFrame
    row: dict[str, float | None] = {}
    for col in risk_cols:
        if col == "Fase_ideal_num":
            row[col] = fase_ideal_num
        elif col == "gap_fase":
            row[col] = gap_fase
        else:
            row[col] = student_data.get(col)

    df_row = pd.DataFrame([row])
    df_row = df_row.apply(pd.to_numeric, errors="coerce")

    #input com média do treino
    for i, col in enumerate(risk_cols):
        if df_row[col].isna().any():
            df_row[col] = mu[i]

    X = df_row[risk_cols].to_numpy(dtype=float)
    X_scaled = (X - mu) / sigma

    #score de risco
    nivel_def = float(df_row["Nível de Defasagem"].iloc[0])
    ida = float(df_row["Indicador de Aprendizagem"].iloc[0])
    ieg = float(df_row["Indicador de Engajamento"].iloc[0])
    ipv = float(df_row["Indicador de Ponto de Virada"].iloc[0])

    def _z(val, col_name):
        idx = risk_cols.index(col_name)
        return (val - mu[idx]) / sigma[idx]

    risk_score = (
        RISK_WEIGHTS["defasagem_risco"] * (-_z(nivel_def, "Nível de Defasagem"))
        + RISK_WEIGHTS["neg_ida"] * (-_z(ida, "Indicador de Aprendizagem"))
        + RISK_WEIGHTS["neg_ieg"] * (-_z(ieg, "Indicador de Engajamento"))
        + RISK_WEIGHTS["neg_ipv"] * (-_z(ipv, "Indicador de Ponto de Virada"))
    )
    risk_score += (not pv_bool) * 0.3

    return X_scaled, float(risk_score), gap_fase


def predict_cluster(X_scaled: np.ndarray, model: dict) -> int:
    """Atribui o cluster mais próximo usando os centroids do modelo."""
    centroids = np.array(model["centroids"])
    d2 = ((X_scaled[:, None, :] - centroids[None, :, :]) ** 2).sum(axis=2)
    return int(d2.argmin(axis=1)[0])


def risk_level_from_score(score: float) -> str:
    """Classifica o nível de risco baseado no risk_score."""
    if score < -0.5:
        return "Baixo"
    elif score < 0.3:
        return "Médio"
    elif score < 1.0:
        return "Alto"
    else:
        return "Crítico"
