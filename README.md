# Passos Mágicos — API de Risco de Defasagem

Motivação
- Dor: escolas e programas educacionais precisam identificar estudantes com risco de defasagem para priorizar intervenções.
- O que o modelo resolve: classifica e pontua o risco de defasagem por estudante (cluster + score) permitindo priorização e monitoramento.

O que este projeto faz (resumo)
- Pipeline de dados e engenharia de features a partir do dataset fornecido em `src/`.
- Treinamento de um modelo KMeans customizado para agrupar alunos por perfil de risco.
- API FastAPI para predição em tempo real e endpoints de monitoramento.
- Dashboard Streamlit com métricas do dataset e distribuição por cluster.

Rotas principais (API)
- `GET /health` — status da API e modelo carregado
- `GET /monitor/status` — health + métricas agregadas
- `GET /monitor/metrics` — métricas por feature (média, std, missing, delta vs mu)
- `POST /predict` — predição para um estudante (JSON)
- `POST /predict/batch` — predição em lote (JSON)
- `GET /docs` — Swagger UI interativo

Portas
- `8000` → API (FastAPI / Uvicorn)
- `8501` → Dashboard (Streamlit)

Quick start (recomendado)
1. Clone o repositório
2. Execute:

```bash
make start
```

Observações sobre `make start`
- Tenta instalar dependências e iniciar localmente. Se a instalação falhar (ex.: compilação de `pydantic-core`), faz fallback para build/run em container; se o container também não estiver disponível, inicia em modo dev (foreground).

Alternativas
- Modo dev (foreground):

```bash
make start-dev
# ou
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
streamlit run monitoring/dashboard.py --server.port 8501 --server.address 0.0.0.0
```

Containers
- Build: `make build`
- Run:   `make run` (o comando monta `./src` no container para garantir `model.pkl` e CSV)

Arquitetura e tecnologias
- Entrypoint API: `app/main.py` (FastAPI, lifespan carrega o modelo)
- Rotas e validação: `app/routes.py`, `app/schemas.py` (Pydantic)
- Lógica de predição: `app/predictor.py` (pré-processamento e score)
- Loader/serialização do modelo: `app/model_loader.py` e `src/model/model.pkl`
- Pipeline de treino/simulação: `src/run_simulation.py`, `src/processing_and_models.py`
- Dashboard: `monitoring/dashboard.py` (Streamlit + Plotly)
- Execução local: `scripts/run_monitor.sh` / `scripts/stop_monitor.sh` (inicia/para API + Streamlit em background)
- Dev / automação: `Makefile` com alvos `install`, `start`, `start-dev`, `build`, `run`, `test`, `logs`.

Dependências
- Versões fixadas em `requirements.txt` para consistência. Observação: em algumas plataformas pode ser necessário instalar toolchains nativos (Xcode CLT, Rust) para compilar dependências como `pydantic-core` se não houver wheel disponível.

Testes
- `make test` (executa `pytest`)

Logs
- `logs/api.log` e `logs/streamlit.log` (quando iniciado pelo script `scripts/run_monitor.sh`)

