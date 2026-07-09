#!/usr/bin/env bash
# Phoenix VPN V10 – obfs4proxy install and systemd service
set -euo pipefail

PHOENIX_DIR="${PHOENIX_DIR:-/opt/phoenix}"
OBFS4_PORT="${OBFS4_PORT:-1080}"
OBFS4_STATE="${OBFS4_STATE:-${PHOENIX_DIR}/obfs4/state}"
OBFS4_CERT="${OBFS4_CERT:-${PHOENIX_DIR}/obfs4/cert}"
OBFS4_BIND="${OBFS4_BIND:-127.0.0.1}"
OBFS4_TARGET="${OBFS4_TARGET:-127.0.0.1:1194}"

log() { echo "[phoenix-obfs4] $*"; }

install_obfs4proxy() {
  export DEBIAN_FRONTEND=noninteractive
  apt-get update -qq
  add-apt-repository -y universe 2>/dev/null || true
  apt-get update -qq

  if apt-cache show obfs4proxy &>/dev/null; then
    apt-get install -y -qq obfs4proxy
    return 0
  fi

  log "Package obfs4proxy not in apt; trying golang install..."
  apt-get install -y -qq golang-go git
  export GOPATH="${GOPATH:-/opt/go}"
  export PATH="${GOPATH}/bin:${PATH}"
  go install gitlab.com/yawning/obfs4.git/obfs4proxy@latest
  ln -sf "${GOPATH}/bin/obfs4proxy" /usr/local/bin/obfs4proxy
}

resolve_binary() {
  if command -v obfs4proxy &>/dev/null; then
    command -v obfs4proxy
    return 0
  fi
  if [[ -x /usr/local/bin/obfs4proxy ]]; then
    echo /usr/local/bin/obfs4proxy
    return 0
  fi
  return 1
}

write_systemd_unit() {
  local binary="$1"
  local launcher="${PHOENIX_DIR}/deploy/obfs4_pt_launcher.py"
  mkdir -p "${OBFS4_STATE}" "${OBFS4_CERT}"
  chmod 700 "${OBFS4_STATE}" "${OBFS4_CERT}"
  chmod +x "${launcher}" 2>/dev/null || true

  cat > /etc/systemd/system/phoenix-obfs4.service <<EOF
[Unit]
Description=Phoenix obfs4proxy bridge for OpenVPN
After=network-online.target openvpn-server@server.service openvpn@server.service
Wants=network-online.target

[Service]
Type=simple
User=root
Environment=OBFS4_STATE=${OBFS4_STATE}
Environment=OBFS4_CERT=${OBFS4_CERT}
Environment=OBFS4_BIND=0.0.0.0
Environment=OBFS4_PORT=${OBFS4_PORT}
Environment=OBFS4_TARGET=${OBFS4_TARGET}
Environment=OBFS4_BINARY=${binary}
ExecStart=/usr/bin/python3 ${launcher}
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

  systemctl daemon-reload
  systemctl enable phoenix-obfs4.service
  systemctl restart phoenix-obfs4.service
}

main() {
  log "Installing obfs4proxy..."
  install_obfs4proxy
  local binary
  binary="$(resolve_binary)" || { log "ERROR: obfs4proxy binary not found"; exit 1; }

  if [[ -f /etc/openvpn/server.conf ]]; then
    local ovpn_port
    ovpn_port="$(grep -E '^port ' /etc/openvpn/server.conf | awk '{print $2}' | head -1)"
    if [[ -n "${ovpn_port}" ]]; then
      OBFS4_TARGET="127.0.0.1:${ovpn_port}"
      log "Targeting OpenVPN at ${OBFS4_TARGET}"
    fi
  fi

  log "Using binary: ${binary}"
  "${binary}" -version 2>&1 || true
  write_systemd_unit "${binary}"
  sleep 2
  if systemctl is-active --quiet phoenix-obfs4.service; then
    log "phoenix-obfs4.service is active on ${OBFS4_BIND}:${OBFS4_PORT}"
  else
    log "WARN: service not active yet (OpenVPN may still be starting)"
  fi
}

main "$@"
