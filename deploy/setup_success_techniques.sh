#!/usr/bin/env bash
# Deploy Esfand 1404 success techniques: openvpn_success, l2tp_success, wireguard_tls
set -euo pipefail

PHOENIX_DIR="${PHOENIX_DIR:-/opt/phoenix}"
CFG="${PHOENIX_DIR}/configs"

log() { echo "[phoenix-success] $*"; }

find_node_dir() {
  local proto="$1"
  local d
  for d in "${CFG}/${proto}"/*/; do
    [[ -f "${d}schema.json" ]] && { echo "${d%/}"; return 0; }
  done
  [[ -f "${CFG}/${proto}/schema.json" ]] && { echo "${CFG}/${proto}"; return 0; }
  return 1
}

setup_openvpn_success() {
  local dir
  dir="$(find_node_dir openvpn_success)" || { log "skip openvpn_success (no config)"; return 0; }
  local schema="${dir}/schema.json"
  local port key
  port="$(python3 -c "import json;print(json.load(open('${schema}'))['server']['port'])")"
  key="$(python3 -c "import json;print(json.load(open('${schema}'))['tls']['key'])")"
  local ovpn_dir="${PHOENIX_DIR}/openvpn-success"
  mkdir -p "${ovpn_dir}" /etc/openvpn

  if [[ ! -f "${ovpn_dir}/ca.crt" ]]; then
    if [[ -d /usr/share/easy-rsa ]]; then
      cp -r /usr/share/easy-rsa "${ovpn_dir}/easy-rsa"
      cd "${ovpn_dir}/easy-rsa"
      ./easyrsa init-pki >/dev/null 2>&1 || true
      EASYRSA_BATCH=1 ./easyrsa build-ca nopass >/dev/null 2>&1 || true
      EASYRSA_BATCH=1 ./easyrsa gen-dh >/dev/null 2>&1 || true
      EASYRSA_BATCH=1 ./easyrsa build-server-full server nopass >/dev/null 2>&1 || true
      cp pki/ca.crt pki/issued/server.crt pki/private/server.key pki/dh.pem "${ovpn_dir}/" 2>/dev/null || true
    fi
  fi

  printf '%s\n' "${key}" > "${ovpn_dir}/tls-crypt-v2.key"
  cat > /etc/openvpn/server-success.conf <<EOF
port ${port}
proto tcp
dev tun
ca ${ovpn_dir}/ca.crt
cert ${ovpn_dir}/server.crt
key ${ovpn_dir}/server.key
dh ${ovpn_dir}/dh.pem
tls-crypt-v2 ${ovpn_dir}/tls-crypt-v2.key
cipher AES-256-GCM
auth SHA256
tls-version-min 1.3
keepalive 10 60
server 10.9.0.0 255.255.255.0
verb 3
EOF

  ufw allow "${port}"/tcp 2>/dev/null || true
  systemctl enable openvpn-server@server-success 2>/dev/null || true
  systemctl restart openvpn-server@server-success 2>/dev/null || \
    openvpn --config /etc/openvpn/server-success.conf --daemon openvpn-success
  log "openvpn_success listening on tcp/${port}"
}

setup_l2tp_success() {
  local dir
  dir="$(find_node_dir l2tp_success)" || { log "skip l2tp_success"; return 0; }
  local schema="${dir}/schema.json"
  local user pass psk
  user="$(python3 -c "import json;print(json.load(open('${schema}'))['auth']['username'])")"
  pass="$(python3 -c "import json;print(json.load(open('${schema}'))['auth']['password'])")"
  psk="$(python3 -c "import json;print(json.load(open('${schema}'))['ipsec']['pre_shared_key'])")"

  cp -f "${dir}/ipsec.conf" /etc/ipsec.conf
  mkdir -p /etc/ppp /etc/xl2tpd
  echo ": PSK \"${psk}\"" > /etc/ipsec.secrets
  cat > /etc/xl2tpd/xl2tpd.conf <<'EOF'
[global]
listen-addr = 0.0.0.0
port = 1701
[lns default]
ip range = 10.10.10.100-10.10.10.200
local ip = 10.10.10.1
require chap = yes
refuse pap = yes
ppp debug = no
pppoptfile = /etc/ppp/options.xl2tpd
length bit = yes
EOF
  cat > /etc/ppp/options.xl2tpd <<'EOF'
require-mschap-v2
ms-dns 1.1.1.1
ms-dns 8.8.8.8
asyncmap 0
auth
crtscts
lock
hide-password
name l2tpd
proxyarp
lcp-echo-interval 30
lcp-echo-failure 4
EOF
  echo "\"${user}\" l2tpd \"${pass}\" *" > /etc/ppp/chap-secrets
  ufw allow 1701/udp 2>/dev/null || true
  ufw allow 4500/udp 2>/dev/null || true
  ufw allow 500/udp 2>/dev/null || true
  systemctl enable strongswan-starter xl2tpd 2>/dev/null || true
  systemctl restart strongswan-starter ipsec xl2tpd 2>/dev/null || true
  log "l2tp_success active (1701/4500)"
}

setup_wireguard_tls() {
  local dir
  dir="$(find_node_dir wireguard_tls)" || { log "skip wireguard_tls"; return 0; }
  local schema="${dir}/schema.json"
  local inner_port
  inner_port="$(python3 -c "import json;print(json.load(open('${schema}'))['wireguard']['inner_port'])")"

  local wg_dir="${PHOENIX_DIR}/wireguard-tls"
  mkdir -p "${wg_dir}" /etc/wireguard
  local srv_priv srv_pub
  srv_priv="$(wg genkey)"
  srv_pub="$(printf '%s' "${srv_priv}" | wg pubkey)"

  cat > /etc/wireguard/wg-tls.conf <<EOF
[Interface]
Address = 10.11.0.1/24
ListenPort = ${inner_port}
PrivateKey = ${srv_priv}
PostUp = iptables -A FORWARD -i %i -j ACCEPT; iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
PostDown = iptables -D FORWARD -i %i -j ACCEPT; iptables -t nat -D POSTROUTING -o eth0 -j MASQUERADE
EOF

  ufw allow "${inner_port}"/udp 2>/dev/null || true
  wg-quick down wg-tls 2>/dev/null || true
  wg-quick up wg-tls

  printf '%s\n' "${srv_pub}" > "${wg_dir}/server_public.key"
  printf '%s\n' "${inner_port}" > "${wg_dir}/listen_port"
  log "wireguard_tls active on udp/${inner_port} (server pubkey saved)"
}

main() {
  mkdir -p "${PHOENIX_DIR}/certs"
  setup_openvpn_success
  setup_l2tp_success
  setup_wireguard_tls
  log "success techniques deploy complete"
}

main "$@"
