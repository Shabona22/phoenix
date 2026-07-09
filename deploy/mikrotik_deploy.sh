#!/usr/bin/env bash
# Deploy Phoenix MikroTik RouterOS scripts via SSH (primary path).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SCRIPTS_DIR="$ROOT/scripts/mikrotik"
IMPORT_ORDER=(dns_cache smart_splitter multi_wan smart_firewall vpn_server mesh_client monitoring)

IP=""
USER="admin"
PASSWORD=""
GENERATE_ONLY=0

usage() {
  echo "Usage: $0 --ip HOST [--user admin] [--password PASS] [--generate-only]"
  exit 1
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --ip) IP="$2"; shift 2 ;;
    --user) USER="$2"; shift 2 ;;
    --password) PASSWORD="$2"; shift 2 ;;
    --generate-only) GENERATE_ONLY=1; shift ;;
    -h|--help) usage ;;
    *) echo "Unknown option: $1"; usage ;;
  esac
done

echo "==> Generating RouterOS scripts"
PYTHONPATH="$ROOT/src" python3 -c "from mikrotik.advanced_config_generator import MikroTikConfigGenerator; MikroTikConfigGenerator().generate_all_scripts()"

if [[ "$GENERATE_ONLY" -eq 1 ]]; then
  echo "==> Generate-only mode; scripts in $SCRIPTS_DIR"
  ls -la "$SCRIPTS_DIR"/*.rsc
  exit 0
fi

[[ -n "$IP" ]] || usage
[[ -n "$PASSWORD" ]] || { echo "ERROR: --password required for deploy"; exit 1; }

if ! command -v sshpass >/dev/null 2>&1; then
  echo "ERROR: sshpass not installed (brew install sshpass)"
  exit 1
fi

SSH_OPTS=(-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null)
SCP="sshpass -p $PASSWORD scp ${SSH_OPTS[*]}"
SSH="sshpass -p $PASSWORD ssh ${SSH_OPTS[*]}"

echo "==> Uploading scripts to $USER@$IP"
for script in "${IMPORT_ORDER[@]}"; do
  file="$SCRIPTS_DIR/${script}.rsc"
  [[ -f "$file" ]] || { echo "Missing $file"; exit 1; }
  $SCP "$file" "$USER@$IP:/${script}.rsc"
done

echo "==> Importing scripts on MikroTik"
for script in "${IMPORT_ORDER[@]}"; do
  echo "  -> /import file-name=${script}.rsc"
  $SSH "$USER@$IP" "/import file-name=${script}.rsc"
done

echo "==> Verification commands (run on router):"
echo "  /log print where message~\"phoenix\""
echo "  /interface wireguard print"
echo "==> Deployment complete"
