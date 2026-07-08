#!/usr/bin/env bash
set -euo pipefail

PHOENIX_DIR="${PHOENIX_DIR:-/opt/phoenix}"
PORTS=(1080 8443 51820 1194 1701 4500)

echo "[phoenix] Health check starting..."

for port in "${PORTS[@]}"; do
  if ss -tln | grep -q ":${port} "; then
    echo "OK  port ${port} listening"
  else
    echo "WARN port ${port} not listening"
  fi
done

if command -v docker &>/dev/null; then
  docker ps --format '{{.Names}}: {{.Status}}' || true
fi

if [ -f "${PHOENIX_DIR}/configs/manifest.json" ]; then
  echo "OK  configs present"
else
  echo "WARN configs missing"
fi

echo "[phoenix] Health check done."
