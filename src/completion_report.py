"""Generate COMPLETION_REPORT.html."""

from __future__ import annotations

import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional


def _run_pytest() -> Dict[str, str]:
    try:
        result = subprocess.run(
            ["python3", "-m", "pytest", "tests/", "-q", "--tb=no"],
            capture_output=True,
            text=True,
            timeout=120,
            cwd=Path(__file__).resolve().parent.parent,
        )
        return {"exit_code": str(result.returncode), "output": result.stdout + result.stderr}
    except Exception as exc:
        return {"exit_code": "error", "output": str(exc)}


def _list_generated_files(output_dir: Path) -> List[str]:
    files = []
    for p in sorted(output_dir.rglob("*")):
        if p.is_file():
            files.append(str(p.relative_to(output_dir)))
    return files


def _get_vm_status() -> Optional[List[Dict]]:
    try:
        from orchestrator.api_client import DopraxClient
        from orchestrator.node_manager import NodeManager

        mgr = NodeManager(DopraxClient())
        nodes = mgr.refresh()
        return [{"name": n.name, "ip": n.ip, "status": n.status, "vm_code": n.vm_code} for n in nodes]
    except Exception:
        return None


def generate_report(output_dir: Optional[str] = None) -> Path:
    base = Path(output_dir or os.getenv("PHOENIX_OUTPUT_DIR", "phoenix-output"))
    base.mkdir(parents=True, exist_ok=True)

    pytest_result = _run_pytest()
    files = _list_generated_files(base)
    vms = _get_vm_status()
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    vm_rows = ""
    if vms:
        for vm in vms:
            vm_rows += f"<tr><td>{vm['name']}</td><td>{vm['ip']}</td><td>{vm['status']}</td><td>{vm['vm_code']}</td></tr>"
    else:
        vm_rows = '<tr><td colspan="4">Could not fetch VM status (API unavailable)</td></tr>'

    file_rows = "\n".join(f"<li>{f}</li>" for f in files[:100])
    if len(files) > 100:
        file_rows += f"<li>... and {len(files) - 100} more</li>"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Phoenix VPN V10 – Completion Report</title>
<style>
body {{ font-family: -apple-system, sans-serif; max-width: 900px; margin: 40px auto; padding: 0 20px; }}
h1 {{ color: #e65100; }}
table {{ border-collapse: collapse; width: 100%; margin: 16px 0; }}
th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
th {{ background: #f5f5f5; }}
.pass {{ color: green; }} .fail {{ color: red; }}
.warn {{ background: #fff3e0; padding: 12px; border-radius: 4px; }}
</style>
</head>
<body>
<h1>Phoenix VPN V10 – Completion Report</h1>
<p>Generated: {now}</p>

<h2>Test Results</h2>
<pre class="{'pass' if pytest_result['exit_code'] == '0' else 'fail'}">{pytest_result['output']}</pre>

<h2>Doprax VMs</h2>
<table>
<tr><th>Name</th><th>IP</th><th>Status</th><th>VM Code</th></tr>
{vm_rows}
</table>

<h2>Generated Files ({len(files)})</h2>
<ul>{file_rows}</ul>

<h2>Protocols</h2>
<ul>
<li>OpenVPN (obfs4 + tls-crypt-v2)</li>
<li>L2TP/IPSec (IKEv1 + NAT-T)</li>
<li>Xray (VLESS/Reality)</li>
<li>Shadowsocks (AEAD)</li>
<li>WireGuard</li>
<li>Hysteria (QUIC)</li>
<li>UDP-over-TCP</li>
</ul>

<div class="warn">
<h3>Security Warnings</h3>
<ul>
<li>Rotate DOPRAX_API_KEY if exposed in chat</li>
<li>Never commit .env to version control</li>
<li>Kill switch requires admin privileges for live enforcement</li>
<li>Bluetooth mesh is scaffold-only on macOS</li>
</ul>
</div>

<h2>Next Steps</h2>
<ol>
<li>Run <code>python3 src/main.py status</code> to verify Doprax connectivity</li>
<li>Run <code>python3 src/main.py generate</code> to produce configs</li>
<li>Run <code>python3 src/main.py provision --name phoenix-node</code> to create new VM</li>
<li>Copy deploy/ to server and run bootstrap.sh</li>
</ol>
</body>
</html>"""

    dest = base / "COMPLETION_REPORT.html"
    dest.write_text(html)
    return dest


if __name__ == "__main__":
    path = generate_report()
    print(f"Report written to {path}")
