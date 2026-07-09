"""Generate SUCCESS_TECHNIQUES_REPORT.html."""

from __future__ import annotations

import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from healer.fallback_manager import FallbackManager


def _run_tests(root: Path) -> tuple[bool, str]:
    result = subprocess.run(
        [
            "python3",
            "-m",
            "pytest",
            "tests/unit/test_dbf_protocols.py",
            "tests/integration/test_simulator.py",
            "-q",
            "--tb=no",
        ],
        capture_output=True,
        text=True,
        cwd=root,
        env={**os.environ, "PYTHONPATH": str(root / "src")},
    )
    out = (result.stdout + result.stderr).strip()
    return result.returncode == 0, out


def generate_report(output_dir: str | None = None) -> Path:
    root = Path(__file__).resolve().parent.parent
    base = Path(output_dir or os.getenv("PHOENIX_OUTPUT_DIR", "phoenix-output"))
    base.mkdir(parents=True, exist_ok=True)
    passed, output = _run_tests(root)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    chain = FallbackManager.PROTOCOL_CHAIN_DBF
    priority_rows = "\n".join(f"<li><code>{p}</code></li>" for p in chain)

    html = f"""<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
  <meta charset="UTF-8">
  <title>SUCCESS TECHNIQUES REPORT</title>
  <style>
    body {{ font-family: -apple-system, sans-serif; max-width: 900px; margin: 40px auto; }}
    .ok {{ color: #2e7d32; font-weight: bold; }}
    .bad {{ color: #c62828; font-weight: bold; }}
    code {{ background: #f5f5f5; padding: 2px 6px; border-radius: 4px; }}
  </style>
</head>
<body>
  <h1>SUCCESS TECHNIQUES REPORT</h1>
  <p>Generated: {now}</p>
  <p>Status: <span class="{'ok' if passed else 'bad'}">{'PASS' if passed else 'FAIL'}</span></p>

  <h2>Technique Priority (Esfand 1404)</h2>
  <ol>
    {priority_rows}
  </ol>

  <h2>Implemented Core Techniques</h2>
  <ul>
    <li><code>openvpn_success</code>: TCP + 443 + TLS 1.3 + tls-crypt-v2</li>
    <li><code>l2tp_success</code>: IPSec + IKEv2 + AES-256 + NAT-T</li>
    <li><code>wireguard_tls</code>: WireGuard over TLS encapsulation</li>
  </ul>

  <h2>Test Output</h2>
  <pre>{output}</pre>
</body>
</html>
"""
    dest = base / "SUCCESS_TECHNIQUES_REPORT.html"
    dest.write_text(html, encoding="utf-8")
    return dest


if __name__ == "__main__":
    report = generate_report()
    print(f"Report written to {report}")
