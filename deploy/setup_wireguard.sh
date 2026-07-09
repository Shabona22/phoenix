#!/usr/bin/env bash
# Phoenix VPN V10 – WireGuard host interface (wg-quick)
set -euo pipefail

PHOENIX_DIR="${PHOENIX_DIR:-/opt/phoenix}"
WG_SRC="${PHOENIX_DIR}/configs/wireguard/wg0.conf"

log() { echo "[phoenix-wireguard] $*"; }

find_wg_conf() {
  if [[ -f "${WG_SRC}" ]]; then
    echo "${WG_SRC}"
    return 0
  fi
  local f
  for f in "${PHOENIX_DIR}/configs/wireguard"/*/wg0.conf; do
    if [[ -f "$f" ]]; then
      echo "$f"
      return 0
    fi
  done
  return 1
}

main() {
  local src
  src="$(find_wg_conf)" || { log "WARN no wg0.conf; skipping"; return 0; }
  mkdir -p /etc/wireguard
  cp -f "${src}" /etc/wireguard/wg0.conf
  chmod 600 /etc/wireguard/wg0.conf
  systemctl enable wg-quick@wg0 2>/dev/null || true
  wg-quick down wg0 2>/dev/null || true
  wg-quick up wg0
  log "WireGuard wg0 up on port $(grep ListenPort /etc/wireguard/wg0.conf | awk '{print $3}')"
}

main "$@"
