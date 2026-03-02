#Carregamento e cache do modelo KMeans em memória.

import pickle
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

_model: dict | None = None

MODEL_PATH = Path(__file__).parent.parent / "src" / "model" / "model.pkl"


def load_model() -> dict:
    """Carrega o modelo do disco (uma vez). Retorna RuntimeError se falhar."""
    global _model
    if _model is not None:
        return _model

    if not MODEL_PATH.exists():
        raise RuntimeError(
            f"Arquivo de modelo não encontrado: {MODEL_PATH}. "
        )

    with open(MODEL_PATH, "rb") as f:
        _model = pickle.load(f)

    logger.info(
        "Modelo carregado | k=%d | features=%s",
        _model["k"],
        _model["risk_cols"],
    )
    return _model


def get_model() -> dict:
    """Retorna o modelo já carregado. Chama load_model se necessário."""
    if _model is None:
        return load_model()
    return _model
