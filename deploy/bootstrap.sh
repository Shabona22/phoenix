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

fix_apt_sources() {
  if grep -rq oracular /etc/apt 2>/dev/null; then
    log "Rewriting EOL oracular apt sources to noble"
    cat > /etc/apt/sources.list <<'EOF'
deb http://archive.ubuntu.com/ubuntu noble main restricted universe multiverse
deb http://archive.ubuntu.com/ubuntu noble-updates main restricted universe multiverse
deb http://archive.ubuntu.com/ubuntu noble-backports main restricted universe multiverse
deb http://security.ubuntu.com/ubuntu noble-security main restricted universe multiverse
EOF
    find /etc/apt/sources.list.d -type f -delete 2>/dev/null || true
  fi
}

install_packages() {
  export DEBIAN_FRONTEND=noninteractive
  fix_apt_sources
  apt-get update -qq || apt-get update -qq -o Acquire::AllowInsecureRepositories=true || true
  add-apt-repository -y universe 2>/dev/null || true
  apt-get update -qq || apt-get update -qq -o Acquire::AllowInsecureRepositories=true || true

  apt-get install -y -qq \
    curl wget unzip jq socat openssl \
    wireguard-tools openvpn easy-rsa \
    strongswan xl2tpd ppp iptables ufw

  apt-get install -y -qq docker.io || true
  apt-get install -y -qq docker-compose-v2 2>/dev/null || \
    apt-get install -y -qq docker-compose-plugin 2>/dev/null || \
    apt-get install -y -qq docker-compose || true

  systemctl enable docker 2>/dev/null || true
  systemctl start docker 2>/dev/null || true
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
  docker compose down 2>/dev/null || docker-compose down 2>/dev/null || true
  if docker compose version &>/dev/null; then
    docker compose pull --ignore-pull-failures 2>/dev/null || true
    docker compose up -d --force-recreate || log "WARN docker compose up failed"
  elif command -v docker-compose &>/dev/null; then
    docker-compose pull 2>/dev/null || true
    docker-compose up -d --force-recreate || log "WARN docker-compose up failed"
  else
    log "WARN docker compose not available; skipping container services"
  fi
  log "Docker step complete"
}

run_host_scripts() {
  bash "${PHOENIX_DIR}/deploy/setup_openvpn.sh" || log "WARN openvpn setup failed"
  bash "${PHOENIX_DIR}/deploy/setup_l2tp.sh" || log "WARN l2tp setup failed"
  bash "${PHOENIX_DIR}/deploy/setup_wireguard.sh" || log "WARN wireguard setup failed"
  bash "${PHOENIX_DIR}/deploy/setup_obfs4.sh" || log "WARN obfs4 setup failed"
}

main() {
  require_root
  log "Bootstrapping Phoenix VPN into ${PHOENIX_DIR}..."
  extract_bundle
  install_packages
  generate_hysteria_certs
  setup_networking
  start_docker_services
  run_host_scripts
  bash "${PHOENIX_DIR}/deploy/health_check.sh" || true
  log "Bootstrap complete."
}

main "$@"
