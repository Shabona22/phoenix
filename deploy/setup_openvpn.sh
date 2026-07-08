#!/usr/bin/env bash
# Phoenix VPN V10 – OpenVPN host setup with PKI
set -euo pipefail

PHOENIX_DIR="${PHOENIX_DIR:-/opt/phoenix}"
OVPN_DIR="${PHOENIX_DIR}/openvpn"
EASYRSA="${OVPN_DIR}/easy-rsa"
CONFIG_SRC="${PHOENIX_DIR}/configs/openvpn"

log() { echo "[phoenix-openvpn] $*"; }

find_server_conf() {
  local f
  for f in "${CONFIG_SRC}"/*/server.conf "${CONFIG_SRC}/server.conf"; do
    if [[ -f "$f" ]]; then
      echo "$f"
      return 0
    fi
  done
  return 1
}

generate_pki() {
  mkdir -p "${OVPN_DIR}"
  if [[ ! -d "${EASYRSA}" ]]; then
    make-cadir "${EASYRSA}" 2>/dev/null || cp -r /usr/share/easy-rsa "${EASYRSA}"
  fi
  cd "${EASYRSA}"
  rm -rf pki
  EASYRSA_BATCH=1 ./easyrsa init-pki 2>/dev/null || true
  EASYRSA_BATCH=1 ./easyrsa build-ca nopass 2>/dev/null || true
  EASYRSA_BATCH=1 ./easyrsa gen-dh 2>/dev/null || true
  EASYRSA_BATCH=1 ./easyrsa build-server-full server nopass 2>/dev/null || true
  EASYRSA_BATCH=1 ./easyrsa gen-tls-crypt-v2-server server 2>/dev/null || \
    openvpn --genkey tls-crypt-v2-server "${OVPN_DIR}/tls-crypt-v2.key" 2>/dev/null || true

  cp -f pki/ca.crt "${OVPN_DIR}/ca.crt" 2>/dev/null || true
  cp -f pki/issued/server.crt "${OVPN_DIR}/server.crt" 2>/dev/null || true
  cp -f pki/private/server.key "${OVPN_DIR}/server.key" 2>/dev/null || true
  cp -f pki/dh.pem "${OVPN_DIR}/dh.pem" 2>/dev/null || true
  [[ -f pki/private/easyrsa-tls-crypt-v2-server.key ]] && \
    cp -f pki/private/easyrsa-tls-crypt-v2-server.key "${OVPN_DIR}/tls-crypt-v2.key" || true
}

install_server() {
  local server_conf
  server_conf="$(find_server_conf)" || { log "WARN no server.conf; skipping"; return 0; }
  mkdir -p /etc/openvpn
  cp -f "${OVPN_DIR}/ca.crt" "${OVPN_DIR}/server.crt" "${OVPN_DIR}/server.key" \
    "${OVPN_DIR}/dh.pem" "${OVPN_DIR}/tls-crypt-v2.key" /etc/openvpn/ 2>/dev/null || true
  sed "s|/opt/phoenix/openvpn|/etc/openvpn|g" "${server_conf}" > /etc/openvpn/server.conf
  systemctl enable openvpn-server@server 2>/dev/null || \
    systemctl enable openvpn@server 2>/dev/null || true
  systemctl restart openvpn-server@server 2>/dev/null || \
    systemctl restart openvpn@server 2>/dev/null || \
    openvpn --config /etc/openvpn/server.conf --daemon
  log "OpenVPN configured"
}

main() {
  generate_pki
  install_server
}

main "$@"
