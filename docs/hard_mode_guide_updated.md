# Hard Mode Guide – Updated (Esfand 1404 – Khordad 1405)

This update reflects real-world censorship patterns observed between Esfand 1404
and Khordad 1405: prolonged international outages, tiered internet, AI/ML
classification, and cloud-provider blocking.

## Threat model

| Threat | Hard Mode response |
|--------|-------------------|
| Full international blackout | QR cards, Mesh P2P, USB export (`AlternativeChannel`) |
| Tiered / domestic-only internet | Personal fixed-IP servers, non-cloud deploy |
| AI/ML traffic classification | Content Simulator + LLM Defender |
| All VPN protocols blocked | DoH tunnel, then SSH/ICMP |
| Cloud VPS blocked | `OrchestratorPersonalServerManager` (fixed IP) |
| 24h+ outage | `AutoHealerEnhanced` (protocol → node → channel → emergency) |

## Updated escalation ladder

```
standard_protocols → content_simulation → ssh_tunnel → icmp_tunnel → doh_tunnel → mesh_p2p
```

## New modules (fixes batch)

### 1. Alternative channels (`offline/alternative_channel.py`)

Fallback order: **mesh → radio → sms → usb**. Exports land in
`phoenix-output/offline_exports/`.

```python
from offline.alternative_channel import AlternativeChannel
alt = AlternativeChannel()
alt.send_config("user-42", {"protocol": "wireguard", "server": {"ip": "10.0.0.1"}})
```

### 2. Enhanced auto-healer (`healer/auto_healer_enhanced.py`)

Polls every 30s; escalates through protocol, node, channel, emergency.

```python
from healer.auto_healer_enhanced import AutoHealerEnhanced
from healer.fallback_manager import FallbackManager
from orchestrator.node_manager import NodeManager

healer = AutoHealerEnhanced(FallbackManager(NodeManager()))
healer.set_connected_check(lambda: False)  # or wire TrafficValidator
healer.attempt_recovery()
```

### 3. DoH tunnel (`protocols/doh_tunnel.py`)

```python
from protocols.doh_tunnel import DoHTunnel
t = DoHTunnel()
t.send_data(b"probe", transport=lambda chunk, q: True)
```

### 4. Personal servers (`orchestrator/personal_server_manager.py`)

```python
from orchestrator.personal_server_manager import OrchestratorPersonalServerManager
mgr = OrchestratorPersonalServerManager()
mgr.add_server("home-vps", "198.51.100.7", username="root", location="TR", fixed_ip=True)
mgr.deploy_to_personal_server("home-vps", {"protocol": "xray"})
```

### 5. Paper configs (`offline/emergency_paper_config.py`)

```python
from offline.emergency_paper_config import EmergencyPaperConfig
EmergencyPaperConfig().generate_bundle("user-1", [{"protocol": "openvpn", "server": {"ip": "1.2.3.4", "port": 1194}}])
```

### 6. Field reports (`monitoring/user_report_collector.py`)

```python
from monitoring.user_report_collector import UserReportCollector
c = UserReportCollector()
c.collect_report({"status": "connected", "protocol": "xray", "latency_ms": 120})
print(c.get_stats())
```

## Test scenarios

| Scenario | Test | Acceptance |
|----------|------|------------|
| Full blackout | QR + Mesh + USB export | Config delivered locally |
| All protocols blocked | `emergency_plan(all_protocols_blocked=True)` | Selects `doh_tunnel` |
| 24h outage | `AutoHealerEnhanced.attempt_recovery()` | Escalates through modes |
| AI classification | Content Simulator + LLM Defender | Realness score ≥ 0.6 |

## Commands

```bash
python3 -m pytest tests/unit/test_fixes.py tests/unit/test_hard_mode.py -q
PYTHONPATH=src python3 src/fixes_report.py
PYTHONPATH=src python3 src/hard_mode_report.py
```

See also: `docs/hard_mode_guide.md` (original), `PHOENIX_FIXES.md`.
