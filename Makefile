VENVDIR=.venv
PY=.

.PHONY: venv install start start-dev stop build run test logs clean

venv:
	python3 -m venv $(VENVDIR)

install: venv
	# atualiza pip/setuptools/wheel (evita falhas ao compilar pydantic-core)
	. $(VENVDIR)/bin/activate && python -m pip install --upgrade pip setuptools wheel build
	. $(VENVDIR)/bin/activate && pip install -r requirements.txt

start:
	mkdir -p logs
	chmod +x scripts/run_monitor.sh scripts/stop_monitor.sh
	# tenta instalar localmente (não falha o make se der erro) e então iniciar localmente.
	# Se qualquer etapa falhar, faz fallback para container; se container falhar, usa start-dev.
	( . $(VENVDIR)/bin/activate 2>/dev/null || true; \
	  python3 -m venv $(VENVDIR) 2>/dev/null || true; \
	  . $(VENVDIR)/bin/activate && python -m pip install --upgrade pip setuptools wheel build ) || echo "warning: upgrade/install step failed, continuing to fallback logic";
	( . $(VENVDIR)/bin/activate && pip install -r requirements.txt ) || echo "warning: pip install failed, will try container fallback";
	( . $(VENVDIR)/bin/activate && ./scripts/run_monitor.sh ) || (echo "Local start failed — attempting container build/run" && (make build && make run || (echo "Container start failed — falling back to start-dev" && make start-dev)))

start-dev:
	. $(VENVDIR)/bin/activate && uvicorn app.main:app --host 0.0.0.0 --port 8000 &
	. $(VENVDIR)/bin/activate && streamlit run monitoring/dashboard.py --server.port 8501 --server.address 0.0.0.0 &

stop:
	@if [ -f scripts/monitor.pid ]; then xargs -r kill -9 < scripts/monitor.pid || true; rm -f scripts/monitor.pid; fi
	pkill -f uvicorn || true
	pkill -f streamlit || true

build:
	# tenta com podman, cai para docker se não disponível
	podman build -t passos-magicos-api . || docker build -t passos-magicos-api .

run:
	# roda container (monta ./src para garantir model + csv)
	podman run --rm -p 8000:8000 -p 8501:8501 -v "$(PWD)/src":/app/src:ro passos-magicos-api || \
		docker run --rm -p 8000:8000 -p 8501:8501 -v "$(PWD)/src":/app/src:ro passos-magicos-api

test:
	. $(VENVDIR)/bin/activate && pytest -q

logs:
	tail -n 200 logs/api.log logs/streamlit.log || true

clean:
	rm -rf $(VENVDIR)
	rm -f scripts/monitor.pid
