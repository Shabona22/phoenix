# Phoenix V10 – DBF Guide

## What is DBF?

**Degradation-Based Filtering** degrades connections instead of hard-blocking immediately:

- injected delay
- packet loss
- jitter
- occasional RST after sustained sessions

TLS fingerprint blocking is increasingly common; no-TLS transports often survive longer under DBF.

## Priority order

1. `websocket_plain`
2. `tcp_plain`
3. `http_upgrade`
4. `openvpn_cloak`
5. `wireguard_amnezia`
6. `l2tp_xray`
7. `xray_reality`
8. legacy protocols (`shadowsocks`, `hysteria`, `xray`, …)

## Modules

| Module | Path | Role |
|---|---|---|
| Degradation simulator | `src/simulator/degradation_simulator.py` | inject DBF effects |
| Iran filter simulator | `src/simulator/iran_filter_simulator.py` | rank protocol stability |
| Config tester | `src/utils/config_tester.py` | test configs in simulator |
| Research Agent | `src/research/research_agent.py` | collect DBF signals |
| Field collector | `src/research/field_data_collector.py` | store user measurements |
| Fingerprint simulator | `src/ai/fingerprint_simulator.py` | JA3/JA4 blocking model |
| Fallback manager | `src/healer/fallback_manager.py` | DBF protocol chain |

## Commands

```bash
PYTHONPATH=src python3 -m pytest tests/unit/test_dbf_simulator.py tests/unit/test_dbf_protocols.py tests/unit/test_dbf_research.py -q
PYTHONPATH=src python3 src/dbf_compliance_report.py
```

Output: `phoenix-output/DBF_COMPLIANCE_REPORT.html`

## Research Agent

When live sources are unavailable, the agent falls back to offline DBF indicators and still recommends no-TLS protocols.

## Production notes

- Validate no-TLS protocols on real Iranian networks before wide rollout.
- Combine with `content_simulator` and `behavioral_morphing` for mixed-traffic camouflage.
- Keep TLS protocols as fallback for regions without DBF.
