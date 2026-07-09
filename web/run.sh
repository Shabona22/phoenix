#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
echo "Phoenix VPN – Panel Starter"
echo "================================"
if [[ -d ../.venv ]]; then
  source ../.venv/bin/activate
fi
pip3 install -q -r requirements_web.txt
export FLASK_DEBUG="${FLASK_DEBUG:-0}"
export PHOENIX_PANEL_PORT="${PHOENIX_PANEL_PORT:-5050}"
echo "Panel URL: http://localhost:${PHOENIX_PANEL_PORT}"
python3 app.py
