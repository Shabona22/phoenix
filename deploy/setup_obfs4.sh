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
  mkdir -p "${OBFS4_STATE}" "${OBFS4_CERT}"
  chmod 700 "${OBFS4_STATE}" "${OBFS4_CERT}"

  cat > /etc/systemd/system/phoenix-obfs4.service <<EOF
[Unit]
Description=Phoenix obfs4proxy bridge for OpenVPN
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=root
Environment=OBFS4_STATE=${OBFS4_STATE}
Environment=OBFS4_CERT=${OBFS4_CERT}
ExecStart=${binary} -enableLogging -logLevel INFO -transparent -server -bindaddr ${OBFS4_BIND}:${OBFS4_PORT} -orport ${OBFS4_TARGET} -cert ${OBFS4_CERT}/cert.pem -iat-mode 0
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
  log "Using binary: ${binary}"
  "${binary}" -version 2>&1 || true
  write_systemd_unit "${binary}"
  sleep 2
  if systemctl is-active --quiet phoenix-obfs4.service; then
    log "phoenix-obfs4.service is active on ${OBFS4_BIND}:${OBFS4_PORT}"
  else
    log "WARN: service not active; run deploy/troubleshoot.sh"
    exit 1
  fi
}

main "$@"
