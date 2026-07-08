#!/usr/bin/env bash
# Phoenix VPN V10 – full server bootstrap
set -euo pipefail

PHOENIX_DIR="${PHOENIX_DIR:-/opt/phoenix}"
DEPLOY_SRC="${DEPLOY_SRC:-$(cd "$(dirname "$0")" && pwd)}"
BUNDLE_DIR="${BUNDLE_DIR:-/tmp/phoenix-bundle}"

log() { echo "[phoenix] $*"; }

require_root() {
  if [[ "${EUID:-$(id -u)}" -ne 0 ]]; then
    log "Re-run as root: sudo bash $0"
    exit 1
  fi
}

install_packages() {
  export DEBIAN_FRONTEND=noninteractive
  apt-get update -qq
  add-apt-repository -y universe 2>/dev/null || true
  apt-get update -qq
  apt-get install -y -qq \
    curl wget unzip jq socat \
    docker.io docker-compose-plugin \
    wireguard-tools openvpn easy-rsa \
    strongswan xl2tpd ppp iptables ufw
  systemctl enable docker
  systemctl start docker
}

flatten_configs() {
  local proto node_dir
  for proto_dir in "${PHOENIX_DIR}/configs"/*/; do
    [[ -d "$proto_dir" ]] || continue
    proto="$(basename "$proto_dir")"
    for node_dir in "${proto_dir}"*/; do
      if [[ -d "$node_dir" && "$(basename "$node_dir")" != "$proto" ]]; then
        cp -f "${node_dir}"* "${proto_dir}" 2>/dev/null || true
        break
      fi
    done
  done
  log "Configs flattened for docker compose"
}

extract_bundle() {
  mkdir -p "${PHOENIX_DIR}/configs" "${PHOENIX_DIR}/logs" "${PHOENIX_DIR}/certs"
  if [[ -f "${BUNDLE_DIR}/manifest.json" ]]; then
    cp -a "${BUNDLE_DIR}/configs/." "${PHOENIX_DIR}/configs/"
    log "Configs extracted from bundle"
  elif [[ -d /tmp/phoenix-deploy/configs ]]; then
    cp -a /tmp/phoenix-deploy/configs/. "${PHOENIX_DIR}/configs/"
    log "Configs copied from /tmp/phoenix-deploy"
  else
    log "WARN no bundle found at ${BUNDLE_DIR}; expecting pre-placed configs"
  fi
  flatten_configs
  cp -a "${DEPLOY_SRC}/." "${PHOENIX_DIR}/deploy/"
  cp "${DEPLOY_SRC}/docker-compose.yml" "${PHOENIX_DIR}/docker-compose.yml"
}

generate_hysteria_certs() {
  if [[ ! -f "${PHOENIX_DIR}/certs/hysteria.crt" ]]; then
  openssl req -x509 -nodes -newkey rsa:2048 \
    -keyout "${PHOENIX_DIR}/certs/hysteria.key" \
    -out "${PHOENIX_DIR}/certs/hysteria.crt" \
    -days 3650 -subj "/CN=phoenix-hysteria" 2>/dev/null
  fi
}

setup_networking() {
  sysctl -w net.ipv4.ip_forward=1
  grep -q 'net.ipv4.ip_forward=1' /etc/sysctl.conf 2>/dev/null || \
    echo 'net.ipv4.ip_forward=1' >> /etc/sysctl.conf
  ufw allow 22/tcp 2>/dev/null || true
  ufw allow 51820/udp 2>/dev/null || true
  ufw allow 1194/tcp 2>/dev/null || true
  ufw allow 1701/udp 2>/dev/null || true
  ufw allow 4500/udp 2>/dev/null || true
}

start_docker_services() {
  cd "${PHOENIX_DIR}"
  docker compose pull --ignore-pull-failures 2>/dev/null || true
  docker compose up -d
  log "Docker services started"
}

run_host_scripts() {
  bash "${PHOENIX_DIR}/deploy/setup_openvpn.sh"
  bash "${PHOENIX_DIR}/deploy/setup_l2tp.sh"
  bash "${PHOENIX_DIR}/deploy/setup_obfs4.sh"
}

main() {
  require_root
  log "Bootstrapping Phoenix VPN into ${PHOENIX_DIR}..."
  install_packages
  extract_bundle
  generate_hysteria_certs
  setup_networking
  start_docker_services
  run_host_scripts
  bash "${PHOENIX_DIR}/deploy/health_check.sh" || true
  log "Bootstrap complete."
}

main "$@"
