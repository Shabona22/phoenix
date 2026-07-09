#!/usr/bin/env bash
set -euo pipefail

PHOENIX_DIR="${PHOENIX_DIR:-/opt/phoenix}"
PORTS=(1080 8443 51820 1194 1701 4500)

read_config_port() {
  local proto="$1" key="$2" fallback="$3"
  local schema="${PHOENIX_DIR}/configs/${proto}/schema.json"
  if [[ -f "${schema}" ]] && command -v jq &>/dev/null; then
    local val
    val="$(jq -r "${key} // empty" "${schema}" 2>/dev/null || true)"
    if [[ -n "${val}" && "${val}" != "null" ]]; then
      echo "${val}"
      return 0
    fi
  fi
  echo "${fallback}"
}

HYSTERIA_PORT="$(read_config_port hysteria '.server.port' 8443)"
WG_PORT="$(read_config_port wireguard '.server.port' 51820)"
PORTS=(1080 "${HYSTERIA_PORT}" "${WG_PORT}" 1194 1701 4500)

echo "[phoenix] Health check starting..."

for port in "${PORTS[@]}"; do
  if ss -tln 2>/dev/null | grep -q ":${port} " || ss -uln 2>/dev/null | grep -q ":${port} "; then
    echo "OK  port ${port} listening"
  else
    echo "WARN port ${port} not listening"
  fi
done

for svc in phoenix-obfs4 openvpn-server@server openvpn@server strongswan-starter xl2tpd; do
  if systemctl is-active --quiet "${svc}" 2>/dev/null; then
    echo "OK  systemd ${svc} active"
  fi
done

if command -v docker &>/dev/null; then
  docker ps --format '{{.Names}}: {{.Status}}' 2>/dev/null | grep phoenix || echo "WARN no phoenix docker containers"
fi

if systemctl is-active --quiet phoenix-obfs4 2>/dev/null; then
  echo "OK  obfs4proxy service active"
else
  echo "WARN obfs4proxy service not active"
fi

if [[ -f "${PHOENIX_DIR}/configs/manifest.json" ]] || [[ -d "${PHOENIX_DIR}/configs/xray" ]]; then
  echo "OK  configs present under ${PHOENIX_DIR}/configs"
else
  echo "WARN configs missing"
fi

echo "[phoenix] Health check done."
