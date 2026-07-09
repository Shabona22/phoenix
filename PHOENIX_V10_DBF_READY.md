# 🔥 PHOENIX VPN V10 – DBF READY

نسخه نهایی بر اساس Degradation-Based Filtering، Research Agent و پروتکل‌های بدون TLS.

## دستورالعمل اجرا در Cursor

```
من می‌خواهم پروژه Phoenix VPN را بر اساس PHOENIX_V10_DBF_READY.md پیاده‌سازی کنم.
اولویت 1: simulator/, protocols/no_tls/, research/
اولویت 2: config_tester, fallback_manager
اولویت 3: scripts و docs
خروجی‌ها در ./phoenix-output
گزارش: DBF_COMPLIANCE_REPORT.html
```

## ساختار DBF

```
src/simulator/          degradation_simulator, iran_filter_simulator
src/protocols/no_tls/   websocket_plain, tcp_plain, http_upgrade
src/research/           research_agent, field_data_collector
src/ai/                 fingerprint_simulator
src/utils/              config_tester
src/healer/             fallback_manager (DBF priority)
```

## اولویت Fallback

1. websocket_plain
2. tcp_plain
3. http_upgrade
4. openvpn_cloak → wireguard_amnezia → l2tp_xray → xray_reality
5. shadowsocks → hysteria → xray → wireguard → openvpn → l2tp

## راه‌اندازی

```bash
PYTHONPATH=src python3 -m pytest tests/ -q
PYTHONPATH=src python3 src/dbf_compliance_report.py
```

## وضعیت

**Production-Ready (DBF)** – no-TLS first, simulator-validated, Research Agent integrated.

جزئیات: `docs/dbf_guide.md`
