#!/usr/bin/env bash
# Phoenix VPN V10 – obfs4proxy and service diagnostics
set -uo pipefail

PHOENIX_DIR="${PHOENIX_DIR:-/opt/phoenix}"
OBFS4_PORT="${OBFS4_PORT:-1080}"
OBFS4_STATE="${OBFS4_STATE:-${PHOENIX_DIR}/obfs4/state}"
OBFS4_CERT="${OBFS4_CERT:-${PHOENIX_DIR}/obfs4/cert}"

section() { echo ""; echo "=== $* ==="; }

section "Binary"
if command -v obfs4proxy &>/dev/null; then
  echo "OK  obfs4proxy at $(command -v obfs4proxy)"
  obfs4proxy -version 2>&1 || echo "WARN version check failed"
elif [[ -x /usr/local/bin/obfs4proxy ]]; then
  echo "OK  obfs4proxy at /usr/local/bin/obfs4proxy"
  /usr/local/bin/obfs4proxy -version 2>&1 || true
else
  echo "FAIL obfs4proxy not installed"
  echo "FIX  run: sudo bash deploy/setup_obfs4.sh"
fi

section "Package"
if dpkg -l obfs4proxy &>/dev/null 2>&1; then
  dpkg -l obfs4proxy | tail -1
else
  echo "INFO obfs4proxy not installed via apt (may be go build)"
fi

section "Directories"
for d in "${OBFS4_STATE}" "${OBFS4_CERT}"; do
  if [[ -d "$d" ]]; then
    echo "OK  $d (perms $(stat -c '%a' "$d" 2>/dev/null || stat -f '%OLp' "$d"))"
  else
    echo "WARN missing $d"
    echo "FIX  mkdir -p $d && chmod 700 $d"
  fi
done

section "systemd phoenix-obfs4"
if systemctl list-unit-files phoenix-obfs4.service &>/dev/null; then
  systemctl status phoenix-obfs4.service --no-pager -l 2>&1 | head -20 || true
else
  echo "FAIL phoenix-obfs4.service not installed"
  echo "FIX  run: sudo bash deploy/setup_obfs4.sh"
fi

section "Port ${OBFS4_PORT}"
if ss -tlnp 2>/dev/null | grep -q ":${OBFS4_PORT} "; then
  echo "OK  port ${OBFS4_PORT} listening"
  ss -tlnp | grep ":${OBFS4_PORT} " || true
else
  echo "WARN port ${OBFS4_PORT} not listening"
  echo "FIX  check journalctl -u phoenix-obfs4; verify OBFS4_TARGET OpenVPN is up"
fi

section "Recent logs"
if systemctl list-unit-files phoenix-obfs4.service &>/dev/null; then
  journalctl -u phoenix-obfs4 --no-pager -n 30 2>&1 || true
fi

section "Common fixes"
cat <<'EOF'
- universe repo missing: sudo add-apt-repository universe && sudo apt update
- port conflict: set OBFS4_PORT=1081 before setup_obfs4.sh
- permission denied on state dir: sudo chmod 700 /opt/phoenix/obfs4/state
- OpenVPN not running: start openvpn first; obfs4 bridges to 127.0.0.1:1194
EOF

echo ""
echo "[phoenix] Troubleshoot complete."
