"""
Endpoints:
  GET  /health        → status da aplicação e modelo
  POST /predict       → predição para um estudante
  POST /predict/batch → predição em lote
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException
from pathlib import Path
import pandas as pd

from app.model_loader import get_model
from app.predictor import preprocess, predict_cluster, risk_level_from_score
from app.schemas import (
    BatchPredictionOutput,
    BatchStudentInput,
    HealthOutput,
    PredictionOutput,
    StudentInput,
)

router = APIRouter()
logger = logging.getLogger(__name__)


# ─── helpers ──────────────────────────────────────────────────────────────────

def _student_to_raw(student: StudentInput) -> dict:
    """Converte o schema de volta aos nomes originais das colunas."""
    return {
        "Nível de Defasagem": student.nivel_defasagem,
        "Fase": student.fase,
        "Fase ideal": student.fase_ideal,
        "Atingiu Ponto de Virada": student.atingiu_ponto_de_virada,
        "Indicador de Aprendizagem": student.indicador_aprendizagem,
        "Indicador de Engajamento": student.indicador_engajamento,
        "Indicador Psicossocial": student.indicador_psicossocial,
        "Indicador de Adequação ao Nível": student.indicador_adequacao,
        "Indicador de Ponto de Virada": student.indicador_ponto_virada,
        "Índice de Desenvolvimento Educacional (INDE)": student.inde,
    }


def _run_prediction(student: StudentInput) -> PredictionOutput:
    model = get_model()
    raw = _student_to_raw(student)

    X_scaled, risk_score, gap_fase = preprocess(raw, model)
    cluster = predict_cluster(X_scaled, model)
    level = risk_level_from_score(risk_score)

    logger.info(
        "Predição | cluster=%d | risk_score=%.4f | risk_level=%s | gap_fase=%s",
        cluster, risk_score, level, gap_fase,
    )

    return PredictionOutput(
        cluster=cluster,
        risk_score=round(risk_score, 4),
        risk_level=level,
        gap_fase=round(gap_fase, 2) if gap_fase is not None else None,
    )


#endpoints
@router.get("/health", response_model=HealthOutput, tags=["Infraestrutura"])
def health():
    """Verifica se a API está no ar e se o modelo foi carregado."""
    try:
        model = get_model()
        return HealthOutput(
            status="ok",
            model_loaded=True,
            model_k=model["k"],
            features=model["risk_cols"],
        )
    except Exception as exc:
        logger.error("Health check falhou: %s", exc)
        return HealthOutput(status="degraded", model_loaded=False)


@router.post("/predict", response_model=PredictionOutput, tags=["Predição"])
def predict(student: StudentInput):
    """
    Recebe os indicadores de um estudante e retorna:
    - **cluster**: grupo de risco (0–4)
    - **risk_score**: pontuação de risco (maior = mais risco)
    - **risk_level**: Baixo | Médio | Alto | Crítico
    - **gap_fase**: defasagem em fases (negativo = adiantado)

    Campos ausentes são imputados com a média do conjunto de treino.
    """
    try:
        return _run_prediction(student)
    except Exception as exc:
        logger.exception("Erro na predição: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/predict/batch", response_model=BatchPredictionOutput, tags=["Predição"])
def predict_batch(payload: BatchStudentInput):
    """
    Predição em lote — recebe uma lista de estudantes e retorna uma predição para cada.
    """
    try:
        predictions = [_run_prediction(s) for s in payload.students]
        return BatchPredictionOutput(predictions=predictions, total=len(predictions))
    except Exception as exc:
        logger.exception("Erro na predição em lote: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


# --- Monitoramento / métricas -------------------------------------------------


@router.get("/monitor/metrics", tags=["Monitoramento"])
def monitor_metrics():
    """Retorna estatísticas simples do dataset e comparação com o modelo treinado.

    - médias e desvios por feature
    - missing rate
    - delta entre média atual e média do treino (mu)
    """
    try:
        try:
            model = get_model()
        except Exception as e:
            logger.warning("Modelo não disponível para monitor/metrics: %s", e)
            return {
                "ok": False,
                "error": "model_not_loaded",
                "detail": "Modelo não foi carregado; verifique src/model/model.pkl ou inicialização do container.",
                "remediation": "Coloque src/model/model.pkl na imagem ou monte ./src no container, ou gere o modelo com src/run_simulation.py --save-model",
            }

        risk_cols = model.get("risk_cols", [])
        mu = list(model.get("mu", []))
        sigma = list(model.get("sigma", []))

        csv_path = Path(__file__).parent.parent / "src" / "base_dados_pede_2024_ajustado.csv"
        if not csv_path.exists():
            logger.warning("Dataset ausente em monitor/metrics: %s", csv_path)
            return {
                "ok": False,
                "error": "dataset_not_found",
                "detail": f"Dataset não encontrado: {csv_path}",
                "remediation": "Monte o diretório ./src no container ou copie o CSV para /app/src/base_dados_pede_2024_ajustado.csv",
            }

        df = pd.read_csv(csv_path)

        features = {}
        for i, col in enumerate(risk_cols):
            if col in df.columns:
                s = pd.to_numeric(df[col], errors="coerce")
                features[col] = {
                    "mean": None if pd.isna(s.mean()) else float(s.mean()),
                    "std": None if pd.isna(s.std()) else float(s.std()),
                    "missing_rate": float(s.isna().mean()),
                    "model_mu": float(mu[i]) if i < len(mu) else None,
                    "model_sigma": float(sigma[i]) if i < len(sigma) else None,
                    "delta_mu": None if pd.isna(s.mean()) or i >= len(mu) else float(s.mean() - mu[i]),
                }
            else:
                features[col] = {"error": "column not present in dataset"}

        resp = {
            "n_rows": int(len(df)),
            "model_k": model.get("k"),
            "features": features,
        }
        return resp
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Erro ao coletar métricas: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))



@router.get("/monitor/status", tags=["Monitoramento"])
def monitor_status():
    """Combina `health` e `monitor/metrics` em uma única resposta.

    - `health`: estado da API e do carregamento do modelo
    - `metrics`: estatísticas do dataset e comparações com o modelo (quando disponíveis)
    """
    try:
        h = health()
        health_obj = h.dict() if hasattr(h, "dict") else h
    except Exception:
        health_obj = {"status": "degraded", "model_loaded": False}

    try:
        metrics = monitor_metrics()
    except HTTPException as he:
        metrics = {"ok": False, "error": "monitor_error", "detail": str(he.detail)}
    except Exception as e:
        metrics = {"ok": False, "error": "monitor_exception", "detail": str(e)}

    return {"health": health_obj, "metrics": metrics}
