#!/usr/bin/env bash
set -euo pipefail

# Start Uvicorn e Streamlit

CSV_PATH="/app/src/base_dados_pede_2024_ajustado.csv"
MODEL_PATH="/app/src/model/model.pkl"

if [ ! -f "$CSV_PATH" ] || [ ! -f "$MODEL_PATH" ]; then
	echo "ERROR: dataset or model not found inside container."
	echo "Expected files:" \
			 "\n - $CSV_PATH" \
			 "\n - $MODEL_PATH"
	echo
	echo "Solutions:"
	echo "1) Rebuild the image from project root so 'src/' is copied into the image:"
	echo "   docker build -t passos-magicos-api ."
	echo "2) Or run the container mounting your local 'src' into the container:"
	echo "   docker run --rm -p 8000:8000 -p 8501:8501 -v \"\$(pwd)/src\":/app/src:ro passos-magicos-api"
	echo "   (or use podman with the equivalent -v flag)"
	exit 1
fi

PORT="${PORT:-8000}"

echo "Starting API (uvicorn) on 0.0.0.0:${PORT}"
uvicorn app.main:app --host 0.0.0.0 --port "$PORT" &
API_PID=$!

# Opcional - desativar Streamlit
if [ "${DISABLE_STREAMLIT:-0}" = "1" ]; then
	echo "DISABLE_STREAMLIT=1 -> skipping Streamlit startup"
	ST_PID=""
else
	echo "Starting Streamlit dashboard on 0.0.0.0:8501"
	streamlit run monitoring/dashboard.py --server.port 8501 --server.address 0.0.0.0 &
	ST_PID=$!
fi


if [ -n "${ST_PID:-}" ]; then
	wait -n "$API_PID" "$ST_PID" || true
else
	wait "$API_PID" || true
fi

kill "$API_PID" 2>/dev/null || true
if [ -n "${ST_PID:-}" ]; then
	kill "$ST_PID" 2>/dev/null || true
fi

echo "One process exited — container shutting down"
exit 0
