# Phoenix VPN V10 Architecture

## Overview

Phoenix VPN V10 is a censorship-resistant orchestration system that manages multi-protocol VPN configurations across Doprax cloud VMs.

## Layers

1. **Orchestrator** – VM lifecycle (Doprax API), config generation, subscription export
2. **Protocols** – Config generators for 6 VPN protocols + UDP-over-TCP
3. **Security** – Kill switch, DNS/IP/WebRTC leak checks, TLS fingerprint rotation
4. **Healer** – Heartbeat monitoring, protocol/node fallback, DoS detection
5. **Verification** – Real traffic validation through proxy
6. **Obfuscation** – SNI rotation, padding, jitter, port rotation, keepalive, behavioral morphing
7. **Offline** – QR backup, mesh connector scaffold

## Data Flow

```
Doprax API → NodeManager → ConfigGenerator → phoenix-output/configs/
                         → SubscriptionManager → phoenix-output/subscriptions/
TrafficValidator → FallbackManager → NodeManager (switch)
```

## Output Directory

All generated artifacts are stored in `phoenix-output/`:
- `configs/` – per-protocol, per-node configs
- `subscriptions/` – base64 URI lists and JSON exports
- `bootstrap/` – deploy bundles
- `qr/` – QR code backups
- `logs/` – application logs
