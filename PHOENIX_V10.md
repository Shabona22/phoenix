# PHOENIX VPN V10 – MASTER EXECUTION FILE

Industrial-grade censorship-resistant VPN orchestration system.

## Execution Priority

1. Core: orchestrator, protocols, security
2. Critical: healer, verification, obfuscation
3. Deploy scripts and tests

## Output Directory

All generated artifacts go to `./phoenix-output/`.

## Protocols

- Xray (VLESS/Reality)
- Shadowsocks (AEAD)
- WireGuard
- OpenVPN (obfs4 + tls-crypt-v2)
- L2TP/IPSec (IKEv1 + NAT-T)
- Hysteria (QUIC)

## Doprax Integration

API client at `src/orchestrator/api_client.py` manages VM lifecycle via `X-API-Key` header.
