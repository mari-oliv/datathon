"""
API de predição de risco de defasagem escolar - Passos Mágicos
FastAPI application entry point
"""

import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import router
from app.model_loader import load_model

# ─── logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("/tmp/app.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)


# ─── lifespan (carrega modelo na inicialização) ────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Iniciando aplicação — carregando modelo...")
    load_model()
    logger.info("Modelo carregado com sucesso.")
    yield
    logger.info("Aplicação encerrada.")


# ─── app ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Passos Mágicos — API de Risco de Defasagem",
    description=(
        "Prediz o cluster de risco de defasagem escolar de estudantes "
        "da Associação Passos Mágicos usando um modelo KMeans customizado."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
