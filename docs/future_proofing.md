# Future Proofing

## Protocol Fallback Chain

Phoenix V10 uses an ordered fallback chain:

1. Xray (VLESS/Reality) – best DPI resistance
2. Shadowsocks (AEAD) – lightweight, widely supported
3. Hysteria (QUIC) – UDP with obfuscation
4. WireGuard – modern, fast
5. OpenVPN (obfs4) – maximum compatibility
6. L2TP/IPSec – legacy device support

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
