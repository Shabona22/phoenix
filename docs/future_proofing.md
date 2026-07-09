# Future Proofing

## Protocol Fallback Chain (DBF Ready)

Phoenix V10 uses a DBF-aware fallback chain:

1. WebSocket plain (no TLS) – highest DBF stability
2. TCP plain (no TLS)
3. HTTP Upgrade (no TLS)
4. OpenVPN + Cloak
5. WireGuard + AmneziaWG
6. L2TP + Xray reverse tunnel
7. Xray Reality
8. Shadowsocks / Hysteria / Xray / WireGuard / OpenVPN / L2TP (legacy)

Set `FallbackManager(dbf_mode=False)` to use the legacy chain.

## Obfuscation Strategy

- SNI rotation every 300 seconds
- Port rotation from CDN-like port pool
- Traffic padding (64–512 bytes)
- Behavioral morphing profiles
- TLS fingerprint rotation (Chrome/Firefox/Safari JA3)

## Offline Resilience

- QR code config backup for air-gapped transfer
- Bootstrap ZIP bundles for manual deployment
- Mesh connector scaffold for Bluetooth (OS-dependent)

## Scaling

- Multi-node support via Doprax API
- Budget alerts for traffic limits
- DoS detection with sliding window

## Known Limitations

- Real DPI bypass requires live network testing from censored regions
- Kill switch needs admin/root for enforcement
- VM creation via API depends on Doprax account permissions
