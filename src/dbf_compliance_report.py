"""Generate DBF_COMPLIANCE_REPORT.html for Phoenix V10."""

from __future__ import annotations

import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from orchestrator.config_generator import ConfigGenerator
from protocols.no_tls.tcp_plain import TCPPlainConfig
from protocols.no_tls.websocket_plain import WebSocketPlainConfig
from research.research_agent import ResearchAgent
from utils.config_tester import ConfigTester

DBF_MODULES = [
    "simulator/degradation_simulator.py",
    "simulator/iran_filter_simulator.py",
    "protocols/no_tls/websocket_plain.py",
    "protocols/no_tls/tcp_plain.py",
    "protocols/no_tls/http_upgrade.py",
    "research/research_agent.py",
    "research/field_data_collector.py",
    "ai/fingerprint_simulator.py",
    "utils/config_tester.py",
    "healer/fallback_manager.py",
]


def _run_pytest() -> Dict[str, str]:
    root = Path(__file__).resolve().parent.parent
    try:
        result = subprocess.run(
            ["python3", "-m", "pytest", "tests/", "-q", "--tb=no"],
            capture_output=True,
            text=True,
            timeout=180,
            cwd=root,
            env={**os.environ, "PYTHONPATH": str(root / "src")},
        )
        return {"exit_code": str(result.returncode), "output": (result.stdout + result.stderr).strip()}
    except Exception as exc:
        return {"exit_code": "error", "output": str(exc)}


def _module_rows(src: Path) -> str:
    rows: List[str] = []
    for rel in DBF_MODULES:
        path = src / rel
        ok = path.is_file()
        rows.append(
            f"<tr><td>{rel}</td><td class=\"{'pass' if ok else 'fail'}\">{'OK' if ok else 'MISSING'}</td></tr>"
        )
    return "\n".join(rows)


def _config_test_rows() -> str:
    tester = ConfigTester(profile="tls_fingerprint")
    configs = [
        WebSocketPlainConfig().generate_config("93.114.98.9"),
        TCPPlainConfig().generate_config("93.114.98.9"),
        {"protocol": "xray", "tls": True},
    ]
    ranked = tester.test_many(configs)
    return "\n".join(
        f"<tr><td>{item['protocol']}</td><td>{item['stability_score']}</td>"
        f"<td class=\"{'pass' if item['passed'] else 'fail'}\">{'PASS' if item['passed'] else 'FAIL'}</td></tr>"
        for item in ranked
    )


def generate_report(output_dir: str | None = None) -> Path:
    root = Path(__file__).resolve().parent.parent
    base = Path(output_dir or os.getenv("PHOENIX_OUTPUT_DIR", "phoenix-output"))
    base.mkdir(parents=True, exist_ok=True)

    pytest_result = _run_pytest()
    passed = pytest_result["exit_code"] == "0"
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    agent = ResearchAgent(sources={})
    research = agent.analyze_findings(agent.collect_data())
    dbf_priority = ConfigGenerator.DBF_PRIORITY

    html = f"""<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
<meta charset="UTF-8">
<title>Phoenix V10 – DBF Compliance Report</title>
<style>
body {{ font-family: -apple-system, sans-serif; max-width: 1000px; margin: 40px auto; padding: 0 20px; }}
h1 {{ color: #1565c0; }}
table {{ border-collapse: collapse; width: 100%; margin: 16px 0; font-size: 14px; }}
th, td {{ border: 1px solid #ddd; padding: 8px; text-align: right; }}
th {{ background: #f5f5f5; }}
.pass {{ color: #2e7d32; font-weight: bold; }}
.fail {{ color: #c62828; font-weight: bold; }}
.banner {{ background: linear-gradient(135deg, #1976d2, #0d47a1); color: white; padding: 20px; border-radius: 8px; }}
</style>
</head>
<body>
<div class="banner">
<h1>Phoenix V10 – DBF Compliance Report</h1>
<p>Generated: {now}</p>
<p>Status: <strong>{'COMPLIANT' if passed else 'NEEDS FIX'}</strong></p>
</div>

<h2>Test Results</h2>
<pre class="{'pass' if passed else 'fail'}">{pytest_result['output']}</pre>

<h2>DBF Module Checklist</h2>
<table>
<tr><th>Module</th><th>Status</th></tr>
{_module_rows(root / 'src')}
</table>

<h2>Protocol Priority (DBF)</h2>
<ol>
{''.join(f'<li><code>{proto}</code></li>' for proto in dbf_priority)}
</ol>

<h2>Simulator Ranking</h2>
<table>
<tr><th>Protocol</th><th>Stability Score</th><th>Result</th></tr>
{_config_test_rows()}
</table>

<h2>Research Agent Recommendations</h2>
<pre>{json.dumps(research['recommendations'], indent=2, ensure_ascii=False)}</pre>

<h2>Conclusion</h2>
<p>Phoenix V10 is configured for Degradation-Based Filtering with no-TLS protocols as first-line transports.</p>
</body>
</html>"""

    dest = base / "DBF_COMPLIANCE_REPORT.html"
    dest.write_text(html, encoding="utf-8")
    return dest


if __name__ == "__main__":
    path = generate_report()
    print(f"Report written to {path}")
