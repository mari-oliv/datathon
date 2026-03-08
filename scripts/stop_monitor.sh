set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PIDFILE="$ROOT/scripts/monitor.pid"

if [ ! -f "$PIDFILE" ]; then
  echo "PID file not found: $PIDFILE"
  exit 0
fi

read API_PID ST_PID < "$PIDFILE" || true

for pid in $API_PID $ST_PID; do
  if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
    kill "$pid" && echo "Stopped $pid"
  else
    echo "Process $pid not running"
  fi
done

rm -f "$PIDFILE"
echo "Monitor stopped."
