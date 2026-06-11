#!/bin/sh
set -eu

# Railway volume mounts are root-owned; use /tmp for writable agent memory.
export TRADINGAGENTS_MEMORY_LOG_PATH="${TRADINGAGENTS_MEMORY_LOG_PATH:-/tmp/tradingagents-memory/trading_memory.md}"
mkdir -p "$(dirname "$TRADINGAGENTS_MEMORY_LOG_PATH")"

if [ "${AUTOTRADER_ENABLED:-true}" = "true" ]; then
  echo "[entry] starting headless autotrader daemon"
  python scripts/autotrader_daemon.py &
fi

exec python run_webui_dash.py --server-name "${SERVER_NAME:-0.0.0.0}" --port "${PORT:-7860}"
