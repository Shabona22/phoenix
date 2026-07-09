#!/bin/bash
set -euo pipefail
echo "🔥 Phoenix VPN - Quick Setup"
echo "=============================="
cd "$(dirname "$0")"
pip3 install -r requirements.txt
pip3 install -r web/requirements_web.txt
if [ ! -f .env ]; then
  cp .env.example .env
  echo "⚠️  Please edit .env with your DOPRAX_API_KEY"
fi
export PYTHONPATH=src
python3 -m pytest tests/ -q
echo "🌐 Starting panel on port ${PHOENIX_PANEL_PORT:-5050}..."
cd web && python3 app.py
