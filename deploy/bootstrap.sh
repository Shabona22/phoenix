#!/usr/bin/env bash
set -euo pipefail

echo "[phoenix] Bootstrapping server..."

export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq curl wget unzip socat obfs4proxy wireguard-tools docker.io docker-compose-plugin

systemctl enable docker
systemctl start docker

mkdir -p /opt/phoenix/{configs,logs}
cp -r /tmp/phoenix-deploy/configs/* /opt/phoenix/configs/ 2>/dev/null || true

if [ -f /opt/phoenix/docker-compose.yml ]; then
  cd /opt/phoenix
  docker compose up -d
fi

echo "[phoenix] Bootstrap complete."
