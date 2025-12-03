#!/bin/sh
echo "[entrypoint] Container starting (TZ=${TZ:-UTC})"

# Start cron (different systems may provide 'service' or 'cron')
echo "[entrypoint] Starting cron daemon..."
if command -v service >/dev/null 2>&1; then
  service cron start || true
else
  cron || true
fi

# optional: show processes (ps requires procps package)
if command -v ps >/dev/null 2>&1; then
  echo "[entrypoint] Processes:"
  ps aux || true
fi

echo "[entrypoint] Starting FastAPI (uvicorn)..."
# Exec uvicorn so the container PID 1 is the server process
exec uvicorn main:app --host 0.0.0.0 --port 8080
