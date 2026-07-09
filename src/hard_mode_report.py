"""Generate COMPLETION_REPORT_HARD_MODE.html."""

from __future__ import annotations

import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict

from hard_mode import HardMode

LAYERS = [
    ("SSH Tunnel", "ssh_tunnel", "Last-resort SOCKS over SSH"),
    ("ICMP Tunnel", "icmp_tunnel", "Backup channel when TCP is blocked"),
    ("Content Simulator", "content_simulator", "Decoy traffic to defeat DPI/LLM"),
    ("LLM Defender", "llm_defender", "Scores realness and reshapes flows"),
    ("Mesh P2P", "mesh_p2p", "LAN config exchange on blackout"),
    ("Personal Servers", "personal_servers", "User-owned fallback servers"),
]


def _run_pytest() -> Dict[str, str]:
    try:
        result = subprocess.run(
            ["python3", "-m", "pytest", "tests/unit/test_hard_mode.py", "-q", "--tb=short"],
            capture_output=True,
            text=True,
            timeout=120,
            cwd=Path(__file__).resolve().parent.parent,
        )
        return {"exit_code": str(result.returncode), "output": result.stdout + result.stderr}
    except Exception as exc:  # noqa: BLE001
        return {"exit_code": "error", "output": str(exc)}


def generate_report(output_dir: str | None = None) -> Path:
    base = Path(output_dir or os.getenv("PHOENIX_OUTPUT_DIR", "phoenix-output"))
    base.mkdir(parents=True, exist_ok=True)

    hm = HardMode()
    readiness = hm.readiness()
    config = hm.generate_config()
    pytest_result = _run_pytest()
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    layer_rows = ""
    for label, key, desc in LAYERS:
        ready = readiness.get(key, False)
        cls = "pass" if ready else "warn-cell"
        state = "READY" if ready else "STANDBY"
        layer_rows += (
            f"<tr><td>{label}</td><td>{desc}</td>"
            f"<td class=\"{cls}\">{state}</td></tr>"
        )

    scenarios = [
        ("Normal", {}),
        ("DPI blocking", {"dpi_blocking": True}),
        ("DPI + LLM", {"dpi_blocking": True, "llm_classification": True}),
        ("TCP blocked", {"tcp_blocked": True}),
        ("Internet down", {"internet_down": True}),
    ]
    scenario_rows = ""
    for name, kwargs in scenarios:
        plan = hm.emergency_plan(**kwargs)
        scenario_rows += (
            f"<tr><td>{name}</td><td><code>{plan['selected']}</code></td>"
            f"<td><small>{plan['reason']}</small></td></tr>"
        )

    ladder = " &rarr; ".join(config["escalation_ladder"])

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Phoenix VPN V10 – Hard Mode Completion Report</title>
<style>
body {{ font-family: -apple-system, sans-serif; max-width: 1000px; margin: 40px auto; padding: 0 20px; }}
h1 {{ color: #b71c1c; }}
h2 {{ color: #37474f; margin-top: 28px; }}
table {{ border-collapse: collapse; width: 100%; margin: 16px 0; font-size: 14px; }}
th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
th {{ background: #f5f5f5; }}
.pass {{ color: green; font-weight: bold; }}
.warn-cell {{ color: #ef6c00; font-weight: bold; }}
.fail {{ color: #c62828; }}
.ladder {{ background: #fbe9e7; padding: 12px 16px; border-radius: 6px; font-family: monospace; }}
pre {{ background: #263238; color: #eceff1; padding: 12px; border-radius: 6px; overflow-x: auto; }}
</style>
</head>
<body>
<h1>Phoenix VPN V10 – Hard Mode</h1>
<p>Generated: {now}</p>

<h2>Layer Readiness</h2>
<table>
<tr><th>Layer</th><th>Purpose</th><th>State</th></tr>
{layer_rows}
</table>
<p><small>STANDBY = implemented and testable, but the runtime prerequisite
(root for ICMP, paramiko for SSH, or registered peers/servers) is not present here.</small></p>

<h2>Escalation Ladder</h2>
<div class="ladder">{ladder}</div>

<h2>Emergency Decisioning</h2>
<table>
<tr><th>Scenario</th><th>Selected Channel</th><th>Reason</th></tr>
{scenario_rows}
</table>

<h2>Hard Mode Test Results</h2>
<pre class="{'pass' if pytest_result['exit_code'] == '0' else 'fail'}">{pytest_result['output']}</pre>

<h2>Full Config Snapshot</h2>
<pre>{json.dumps(config, indent=2, ensure_ascii=False)}</pre>

<h2>Notes</h2>
<ul>
<li>No external models are used; all logic is internal Python.</li>
<li>No sockets bind and no connections open at import time.</li>
<li>Content Simulator emits decoy payloads only; it never exfiltrates real data.</li>
</ul>
</body>
</html>"""

    dest = base / "COMPLETION_REPORT_HARD_MODE.html"
    dest.write_text(html)
    return dest


if __name__ == "__main__":
    path = generate_report()
    print(f"Hard Mode report written to {path}")
