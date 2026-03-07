## Passos Mágicos — Projeto: Limpeza, Processamento e Modelo

**Resumo / Objetivo**
- Problema: prever o risco de defasagem escolar de estudantes da Associação Passos Mágicos.
- Solução: pipeline completo de ML (pré-processamento → engenharia de features → treinamento KMeans → API para predição).

**Stack tecnológica**
- Python 3.x
- pandas, numpy
- FastAPI para a API
- pickle para serialização do modelo
- pytest para testes
- Docker para empacotamento

---

## Estrutura do projeto (principais arquivos)
- `app/` : código da API (entrypoint `app/main.py`, `app/routes.py`, `app/predictor.py`, `app/model_loader.py`, `app/schemas.py`).
- `src/` : scripts e notebooks de processamento e treinamento (`processing_and_models.py`, `data_cleaning.py`, `base_dados_pede_2024_ajustado.csv`).
- `src/model/model.pkl` : modelo serializado usado pela API.
- `docs/swagger.yaml` : definição OpenAPI/Swagger.
- `tests/` : testes unitários existentes (`test_data_cleaning.py`, `test_processing_and_models.py`).

---

## Como treinar o modelo (local)
1. Crie e ative um ambiente virtual (recomendado):

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Execute o script de treino/simulação (gera clusters e calcula métricas):

```bash
python src/run_simulation.py
```

Observação: o repositório já contém `src/model/model.pkl` usado pela API. Para treinar e salvar o modelo gerado, há uma flag CLI que grava um `model.pkl` compatível com a API.

### Salvar modelo treinado

```bash
# treina e salva em src/model/model.pkl
python src/run_simulation.py --save-model

# ou usar o helper
python scripts/save_model.py
```

---

## Como rodar a API localmente

1. Com ambiente virtual ativo e dependências instaladas:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

2. Usando container (API + Dashboard juntos)

Observação: a imagem foi configurada para iniciar a API (`uvicorn`) e o dashboard Streamlit (`monitoring/dashboard.py`) no mesmo container. O `Dockerfile` expõe as portas `8000` (API) e `8501` (Streamlit). Antes de buildar, confirme que `src/model/model.pkl` está presente e atualizado.

Build da imagem:

```bash
# com Podman (recomendado se o Docker tiver conflito de versão)
podman build -t passos-magicos-api .

# ou com Docker
docker build -t passos-magicos-api .
```

Rodar o container (foreground):

```bash
podman run --rm -p 8000:8000 -p 8501:8501 passos-magicos-api
# ou com Docker
docker run --rm -p 8000:8000 -p 8501:8501 passos-magicos-api
```

Rodar em background (detached):

```bash
podman run -d --name passos-api -p 8000:8000 -p 8501:8501 passos-magicos-api
podman logs -f passos-api

# ou Docker
docker run -d --name passos-api -p 8000:8000 -p 8501:8501 passos-magicos-api
docker logs -f passos-api
```

O entrypoint da imagem inicia ambos os processos; se um encerrar, o container também encerra.

Se usar `docker-compose.yml`, a porta `8501` já está mapeada e você pode subir com:

```bash
docker compose up --build
```

Rápido — URLs e testes após o container subir:

- API health: http://localhost:8000/health
- Swagger (docs): http://localhost:8000/docs
- Dashboard Streamlit: http://localhost:8501

- Teste rápido via curl:

```bash
curl -s http://localhost:8000/health | jq
curl -s -X POST http://localhost:8000/predict -H 'Content-Type: application/json' -d '{"Nível de Defasagem": -1, "Fase":7}'
```

3. Documentação interativa (Swagger) disponível em: `http://localhost:8000/docs`

---

## Exemplos de chamadas à API

- Health check:

```bash
curl -s http://localhost:8000/health | jq
```

- Predição (única):

```bash
curl -s -X POST http://localhost:8000/predict \
	-H 'Content-Type: application/json' \
	-d '{
		"Nível de Defasagem": -1,
		"Fase": 7,
		"Fase ideal": "Fase 8",
		"Atingiu Ponto de Virada": "Não",
		"Indicador de Aprendizagem": 4.0,
		"Indicador de Engajamento": 4.1,
		"Indicador Psicossocial": 5.6,
		"Indicador de Adequação ao Nível": 5.0,
		"Indicador de Ponto de Virada": 7.278,
		"Índice de Desenvolvimento Educacional (INDE)": 5.783
	}'
```

- Predição em lote: enviar `{ "students": [ {...}, {...} ] }` para `/predict/batch`.

---

## Passos do pipeline de Machine Learning
- Pré-processamento dos dados (`src/data_cleaning.py`, notebooks em `src/`)
- Engenharia de features (ver `src/processing_and_models.py` e `src/run_simulation.py`)
- Padronização (média/desvio)
- Treinamento KMeans (implementação em `src/processing_and_models.py`)
- Avaliação: inércia e inspeção de `cluster_card5`
- Serialização do modelo: `src/model/model.pkl` (pickle)

---

## Testes e cobertura
- Executar testes: `pytest -v`
- Checar cobertura: `pytest --cov --cov-report=term-missing`
- Requisito do datathon: cobertura mínima de 80% (atualizar/expandir testes conforme necessário).

---

## Monitoramento e logs
- A aplicação grava logs em `/tmp/app.log` e também envia para stdout.
- Para monitoramento de drift, recomenda-se adicionar um job que armazene estatísticas de features (média, var) periodicamente e visualize num dashboard.

### Dashboard de Monitoramento (Streamlit)

Um dashboard simples foi adicionado em `monitoring/dashboard.py`. Ele carrega `src/model/model.pkl` e `src/base_dados_pede_2024_ajustado.csv` e mostra:
- estatísticas por feature (média, desvio, missing rate)
- comparação entre média atual e média do treino (delta)
- distribuição aproximada por cluster aplicando os centroides do modelo

Instalação e execução:
```bash
pip install streamlit plotly
streamlit run monitoring/dashboard.py
```

O dashboard também pode consumir o endpoint `GET /monitor/metrics` exposto pela API (se a API estiver rodando em `localhost:8000`).

### Executar API + Dashboard localmente em background (scripts)

O repositório traz dois scripts para iniciar/parar a API e o dashboard em background (`.venv` é ativado se presente):

```bash
chmod +x scripts/run_monitor.sh scripts/stop_monitor.sh
./scripts/run_monitor.sh   # inicia uvicorn + streamlit em background
./scripts/stop_monitor.sh  # para os processos
```

Logs são gravados em `logs/api.log` e `logs/streamlit.log`.

---

## Observações e lacunas identificadas (sugestões rápidas)
- O repositório já implementa: pipeline de pré-processamento, KMeans customizado, API FastAPI e testes unitários de utilitários.
- Falta um step automático que serializa o modelo gerado por `run_simulation.py` em `src/model/model.pkl` (hoje o `model.pkl` já existe, mas não há comando documentado para regenerá-lo).
- Documentação no README foi ampliada para atender aos itens do anexo; recomendo adicionar um pequeno script `scripts/save_model.py` para salvar o modelo após treino.

Se quiser, eu atualizo o `run_simulation.py` para salvar automaticamente `src/model/model.pkl` e adiciono um exemplo de `scripts/save_model.py` e um comando Makefile.

Se quiser, eu atualizo o `run_simulation.py` para salvar automaticamente `src/model/model.pkl` e adiciono um exemplo de `scripts/save_model.py` e um comando Makefile.

## Deploy

- A API será deployada no Render.
