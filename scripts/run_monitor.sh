set -euo pipefail

# Inicia a API (uvicorn) e o Streamlit dashboard em background.
# Logs em logs/api.log e logs/streamlit.log. Salva PIDs em scripts/monitor.pid

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VENV="$ROOT/.venv"
LOGDIR="$ROOT/logs"
PIDFILE="$ROOT/scripts/monitor.pid"

mkdir -p "$LOGDIR"

# ativa venv se existir
if [ -f "$VENV/bin/activate" ]; then
  source "$VENV/bin/activate"
fi

API_LOG="$LOGDIR/api.log"
STREAMLIT_LOG="$LOGDIR/streamlit.log"

echo "Iniciando API (uvicorn) ..."
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 >"$API_LOG" 2>&1 &
API_PID=$!

echo "Iniciando Streamlit (dashboard) ..."
nohup streamlit run monitoring/dashboard.py --server.port 8501 --server.address 0.0.0.0 >"$STREAMLIT_LOG" 2>&1 &
ST_PID=$!

echo "$API_PID $ST_PID" > "$PIDFILE"

echo "Started. API PID=$API_PID, Streamlit PID=$ST_PID"
echo "API logs: $API_LOG"
echo "Streamlit logs: $STREAMLIT_LOG"

mkdir -p logs
chmod +x scripts/run_monitor.sh
./scripts/run_monitor.sh
