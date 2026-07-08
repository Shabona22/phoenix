"""Generate COMPLETION_REPORT.html."""

from __future__ import annotations

import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

PROTOCOLS = ["openvpn", "l2tp", "xray", "shadowsocks", "wireguard", "hysteria"]
SERVER_FILES = {
    "xray": "config.json",
    "shadowsocks": "config.json",
    "hysteria": "config.yaml",
    "wireguard": "wg0.conf",
    "openvpn": "server.conf",
    "l2tp": "l2tp_bundle.conf",
}


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


def _get_nodes() -> Optional[Dict[str, List[Dict[str, Any]]]]:
    try:
        from orchestrator.api_client import DopraxClient
        from orchestrator.node_manager import NodeManager

        mgr = NodeManager(DopraxClient())
        mgr.refresh()
        active = [
            {
                "name": n.name,
                "ip": n.ip,
                "status": n.status,
                "vm_code": n.vm_code,
                "location": f"{n.country}/{n.location_name}",
                "excluded": False,
            }
            for n in mgr.list_nodes()
        ]
        excluded = [
            {
                "name": n.name,
                "ip": n.ip,
                "status": n.status,
                "vm_code": n.vm_code,
                "location": f"{n.country}/{n.location_name}",
                "excluded": True,
            }
            for n in mgr.list_all_nodes()
            if n.is_excluded
        ]
        return {"active": active, "excluded": excluded}
    except Exception:
        return None


def _protocol_status(output_dir: Path, vm_code: str) -> Dict[str, str]:
    status: Dict[str, str] = {}
    for proto in PROTOCOLS:
        proto_dir = output_dir / "configs" / proto / vm_code
        server_file = SERVER_FILES.get(proto, "server.conf")
        if (proto_dir / server_file).exists():
            status[proto] = "OK"
        elif proto_dir.exists():
            status[proto] = "PARTIAL"
        else:
            status[proto] = "MISSING"
    return status


def _load_deploy_results(output_dir: Path) -> Dict[str, str]:
    results_file = output_dir / "deploy_results.json"
    if not results_file.exists():
        return {}
    try:
        return json.loads(results_file.read_text())
    except Exception:
        return {}


def generate_report(output_dir: Optional[str] = None) -> Path:
    base = Path(output_dir or os.getenv("PHOENIX_OUTPUT_DIR", "phoenix-output"))
    base.mkdir(parents=True, exist_ok=True)

    pytest_result = _run_pytest()
    files = _list_generated_files(base)
    nodes_data = _get_nodes()
    deploy_results = _load_deploy_results(base)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    active_rows = ""
    excluded_rows = ""
    proto_rows = ""

    if nodes_data:
        for vm in nodes_data["active"]:
            protos = _protocol_status(base, vm["vm_code"])
            proto_summary = ", ".join(f"{k}:{v}" for k, v in protos.items())
            deploy_status = deploy_results.get(vm["vm_code"], "not deployed")
            active_rows += (
                f"<tr><td>{vm['name']}</td><td>{vm['location']}</td>"
                f"<td>{vm['ip']}</td><td>{vm['status']}</td>"
                f"<td>{deploy_status}</td><td><small>{proto_summary}</small></td></tr>"
            )
            for proto, st in protos.items():
                proto_rows += (
                    f"<tr><td>{vm['name']}</td><td>{proto}</td>"
                    f"<td class=\"{'pass' if st == 'OK' else 'fail'}\">{st}</td></tr>"
                )
        for vm in nodes_data["excluded"]:
            excluded_rows += (
                f"<tr><td>{vm['name']}</td><td>{vm['location']}</td>"
                f"<td>{vm['ip']}</td><td>{vm['status']}</td></tr>"
            )
    else:
        active_rows = '<tr><td colspan="6">Could not fetch VM status (API unavailable)</td></tr>'

    file_rows = "\n".join(f"<li>{f}</li>" for f in files[:80])
    if len(files) > 80:
        file_rows += f"<li>... and {len(files) - 80} more</li>"

    deploy_section = ""
    if deploy_results:
        deploy_section = "<h2>Remote Deploy Results</h2><pre>" + "\n".join(
            f"{k}: {v[:500]}" for k, v in deploy_results.items()
        ) + "</pre>"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Phoenix VPN V10 – Completion Report</title>
<style>
body {{ font-family: -apple-system, sans-serif; max-width: 1000px; margin: 40px auto; padding: 0 20px; }}
h1 {{ color: #e65100; }}
table {{ border-collapse: collapse; width: 100%; margin: 16px 0; font-size: 14px; }}
th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
th {{ background: #f5f5f5; }}
.pass {{ color: green; }} .fail {{ color: #c62828; }}
.warn {{ background: #fff3e0; padding: 12px; border-radius: 4px; margin: 16px 0; }}
small {{ color: #555; }}
</style>
</head>
<body>
<h1>Phoenix VPN V10 – Completion Report</h1>
<p>Generated: {now}</p>

<h2>Test Results</h2>
<pre class="{'pass' if pytest_result['exit_code'] == '0' else 'fail'}">{pytest_result['output']}</pre>

<h2>Active Nodes (DE/FR excluded)</h2>
<table>
<tr><th>Name</th><th>Location</th><th>IP</th><th>Status</th><th>Deploy</th><th>Protocols</th></tr>
{active_rows}
</table>

<h2>Excluded Nodes</h2>
<table>
<tr><th>Name</th><th>Location</th><th>IP</th><th>Status</th></tr>
{excluded_rows or '<tr><td colspan="4">None</td></tr>'}
</table>

<h2>Protocol Config Status</h2>
<table>
<tr><th>Node</th><th>Protocol</th><th>Daemon Config</th></tr>
{proto_rows or '<tr><td colspan="3">No configs generated</td></tr>'}
</table>

{deploy_section}

<h2>Generated Files ({len(files)})</h2>
<ul>{file_rows}</ul>

<div class="warn">
<h3>Security</h3>
<ul>
<li>Rotate DOPRAX_API_KEY if exposed in chat</li>
<li>.env and phoenix-output/ must never be committed</li>
<li>Install pre-commit guard: <code>cp scripts/pre-commit-secrets.sh .git/hooks/pre-commit</code></li>
</ul>
</div>

<h2>Next Steps</h2>
<ol>
<li><code>python3 src/main.py status</code> – verify nodes</li>
<li><code>python3 src/main.py generate</code> – regenerate configs</li>
<li><code>python3 deploy/remote_deploy.py</code> – SSH deploy to active nodes</li>
<li><code>bash deploy/troubleshoot.sh</code> – obfs4 diagnostics on server</li>
</ol>
</body>
</html>"""

    dest = base / "COMPLETION_REPORT.html"
    dest.write_text(html)
    return dest


if __name__ == "__main__":
    path = generate_report()
    print(f"Report written to {path}")
