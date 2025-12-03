#!/bin/bash
set -euo pipefail

echo "[entrypoint] Container starting (TZ=${TZ:-UTC})"

# Configure localtime (best-effort)
if [ -n "${TZ:-}" ]; then
  if [ -f "/usr/share/zoneinfo/$TZ" ]; then
    ln -snf /usr/share/zoneinfo/$TZ /etc/localtime || true
    echo "$TZ" > /etc/timezone || true
  fi
fi

# Ensure /data exists and permissions
mkdir -p /data
chmod 755 /data || true

# Start cron (Debian style)
echo "[entrypoint] Starting cron daemon..."
service cron start || {
  # fallback to cron if service command not present
  cron || true
}

# Optional: show cron status
ps aux | grep cron || true

echo "[entrypoint] Starting FastAPI (uvicorn)..."
# Exec so uvicorn receives signals (PID 1)
exec uvicorn main:app --host 0.0.0.0 --port 8080

