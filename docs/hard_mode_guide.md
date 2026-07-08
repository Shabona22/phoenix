# Hard Mode Guide

Hard Mode is Phoenix VPN's last line of defense for extreme censorship: aggressive
DPI, ML/LLM traffic classification, TCP blocking, or total internet blackout.

All layers are pure-Python, dependency-light, and safe to import/test without root
or a live network. Real network activity only happens when you explicitly start it.

## Layers

| Layer | Module | Activates when |
|-------|--------|----------------|
| Content Simulator | `obfuscation/content_simulator.py` | A classifier (DPI/LLM) is active |
| LLM Defender | `hard_mode/llm_defender.py` | Traffic scores as "synthetic" |
| SSH Tunnel | `protocols/ssh_tunnel.py` | Main protocols blocked (last resort) |
| ICMP Tunnel | `protocols/icmp_tunnel.py` | TCP blocked (backup of SSH) |
| Mesh P2P | `offline/mesh_connector.py` (`MeshP2P`) | Full internet blackout |
| Personal Servers | `hard_mode/personal_server_manager.py` | Managed fleet unreachable |

## Escalation ladder

```
standard_protocols → content_simulation → ssh_tunnel → icmp_tunnel → mesh_p2p
```

`EmergencyFallback.plan(conditions)` picks the right tier; `escalate(current)`
steps one tier down when the current channel fails.

## Quick start

```python
from hard_mode import HardMode

hm = HardMode()
print(hm.readiness())                                  # per-layer availability
plan = hm.emergency_plan(dpi_blocking=True, llm_classification=True)
print(plan["selected"])                                # -> "ssh_tunnel"
cfg = hm.generate_config()                             # full serializable config
```

## Personal servers

Register servers you control as the final fallback tier:

```python
from hard_mode.personal_server_manager import PersonalServer, PersonalServerManager

mgr = PersonalServerManager()          # stored in phoenix-output/personal_servers.json
mgr.add(PersonalServer(name="home", ip="198.51.100.7", username="root", trusted=True))
mgr.save()
```

## SSH tunnel (last resort)

```python
from protocols.ssh_tunnel import SSHTunnel

t = SSHTunnel("<ip>", "root", password="<pass>")
if t.connect():
    t.start_persistent(local_port=10808)   # SOCKS5 on 127.0.0.1:10808, self-healing
```

`paramiko` is optional; if missing, `connect()` returns `False` with
`last_error == "paramiko not installed"` instead of raising.

## ICMP tunnel (TCP-blocked backup)

Requires root / `CAP_NET_RAW`. Use `ICMPTunnel.available()` to check first.
`build_packet(payload)` frames data into ICMP echo requests with a valid checksum.

## Mesh P2P (blackout)

```python
from offline.mesh_connector import MeshP2P

mesh = MeshP2P(local_port=8080)
mesh.set_config_provider(lambda: {"proto": "wireguard", "...": "..."})
mesh.start_server()                      # binds only here
mesh.discover_peers(["192.168.1.10"])    # explicit candidates
```

Message types: `ping`/`pong`, `config_request`/`config`, `ack`, `error`.
`handle_message()` is pure (no I/O) and unit-tested.

## Safety notes

- Content Simulator generates decoy payloads only; it does not exfiltrate real data.
- Nothing binds sockets or connects at import time.
- Report: `PYTHONPATH=src python3 src/hard_mode_report.py` →
  `phoenix-output/COMPLETION_REPORT_HARD_MODE.html`.
