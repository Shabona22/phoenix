# PHOENIX V10 ALL PROTOCOLS (DBF)

نسخه یکپارچه پروتکل‌ها با اولویت DBF:

1. `websocket_plain`
2. `tcp_plain`
3. `http_upgrade`
4. `openvpn_cloak`
5. `wireguard_amnezia`
6. `l2tp_xray`
7. `xray_reality`
8. `shadowsocks`
9. `hysteria`

## وضعیت معماری

- OpenVPN خالص: مسدود → `openvpn_cloak`
- WireGuard خالص: مسدود → `wireguard_amnezia`
- L2TP خالص: مسدود → `l2tp_xray`
- TLS fingerprint-sensitive پروتکل‌ها به انتهای fallback منتقل شده‌اند.

## اجزای اصلی

- `src/protocols/no_tls/` (اولویت 1 تا 3)
- `src/protocols/openvpn_cloak.py`
- `src/protocols/wireguard_amnezia.py`
- `src/protocols/l2tp_xray_tunnel.py`
- `src/protocols/xray_reality.py`
- `src/healer/fallback_manager.py`
- `src/simulator/degradation_simulator.py`
- `src/research/research_agent.py`

## گزارش

```bash
PYTHONPATH=src python3 src/dbf_compliance_report.py
```

خروجی: `phoenix-output/DBF_COMPLIANCE_REPORT.html`
