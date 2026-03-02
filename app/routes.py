"""
Endpoints:
  GET  /health        → status da aplicação e modelo
  POST /predict       → predição para um estudante
  POST /predict/batch → predição em lote
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

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
