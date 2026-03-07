# ─── Build stage ──────────────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /app

# instala dependências em layer separado para cache eficiente
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt


# ─── Runtime stage ────────────────────────────────────────────────────────────
FROM python:3.11-slim

WORKDIR /app

# copia pacotes instalados do builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# cria usuário não-root antes de copiar arquivos
RUN useradd -m appuser

# copia código da aplicação com ownership correto para o appuser
COPY --chown=appuser:appuser app/       ./app/
COPY --chown=appuser:appuser src/       ./src/
COPY --chown=appuser:appuser monitoring/ ./monitoring/
COPY --chown=appuser:appuser scripts/   ./scripts/

# variáveis de ambiente
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

EXPOSE 8000
EXPOSE 8501

USER appuser

# healthcheck integrado (Docker verifica a cada 30s)
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Entrypoint que inicia API (uvicorn) e Streamlit
RUN chmod +x ./scripts/docker_entrypoint.sh || true
CMD ["/bin/bash", "./scripts/docker_entrypoint.sh"]
