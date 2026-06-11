#!/bin/sh
set -eu

if [ "${AUTOTRADER_ENABLED:-true}" = "true" ]; then
  echo "[entry] starting headless autotrader daemon"
  python scripts/autotrader_daemon.py &
fi

exec python run_webui_dash.py --server-name "${SERVER_NAME:-0.0.0.0}" --port "${PORT:-7860}"
