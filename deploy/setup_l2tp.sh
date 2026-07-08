#!/usr/bin/env bash
# Phoenix VPN V10 – L2TP/IPsec host setup
set -euo pipefail

PHOENIX_DIR="${PHOENIX_DIR:-/opt/phoenix}"
CONFIG_SRC="${PHOENIX_DIR}/configs/l2tp"
L2TP_DIR="${PHOENIX_DIR}/l2tp"

log() { echo "[phoenix-l2tp] $*"; }

find_bundle() {
  local f
  for f in "${CONFIG_SRC}"/*/l2tp_bundle.conf "${CONFIG_SRC}/l2tp_bundle.conf"; do
    if [[ -f "$f" ]]; then
      echo "$f"
      return 0
    fi
  done
  return 1
}

split_bundle() {
  local bundle="$1"
  mkdir -p "${L2TP_DIR}"
  awk '
    /^### / { file=$2; next }
    file=="ipsec.conf" { print > "'"${L2TP_DIR}"'/ipsec.conf" }
    file=="xl2tpd.conf" { print > "'"${L2TP_DIR}"'/xl2tpd.conf" }
    file=="secrets" { print > "'"${L2TP_DIR}"'/secrets.tmp" }
  ' "${bundle}"
  if [[ -f "${L2TP_DIR}/secrets.tmp" ]]; then
    awk '/ipsec.secrets/,0' "${L2TP_DIR}/secrets.tmp" | grep -v '^#' > /etc/ipsec.secrets 2>/dev/null || \
      grep PSK "${L2TP_DIR}/secrets.tmp" >> /etc/ipsec.secrets 2>/dev/null || true
    awk '/chap-secrets/,0' "${L2TP_DIR}/secrets.tmp" | grep -v '^#' | grep -v PSK > /etc/ppp/chap-secrets 2>/dev/null || true
    rm -f "${L2TP_DIR}/secrets.tmp"
  fi
}

install_configs() {
  local bundle
  bundle="$(find_bundle)" || { log "WARN no l2tp bundle; skipping"; return 0; }
  split_bundle "${bundle}"
  [[ -f "${L2TP_DIR}/ipsec.conf" ]] && cp -f "${L2TP_DIR}/ipsec.conf" /etc/ipsec.conf
  [[ -f "${L2TP_DIR}/xl2tpd.conf" ]] && cp -f "${L2TP_DIR}/xl2tpd.conf" /etc/xl2tpd/xl2tpd.conf
  cat > /etc/ppp/options.xl2tpd <<'EOF'
require-mschap-v2
ms-dns 1.1.1.1
ms-dns 8.8.8.8
asyncmap 0
auth
crtscts
lock
hide-password
modem
debug
name l2tpd
proxyarp
lcp-echo-interval 30
lcp-echo-failure 4
EOF
  systemctl enable strongswan-starter xl2tpd 2>/dev/null || true
  systemctl restart strongswan-starter ipsec xl2tpd 2>/dev/null || true
  log "L2TP/IPsec configured"
}

main() {
  install_configs
}

main "$@"
