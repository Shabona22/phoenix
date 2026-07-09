"""Generate AUTO_ADAPT_REPORT.html."""

from __future__ import annotations

import json
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
            "tests/unit/test_auto_adapt.py",
            "tests/unit/test_auto_adapt_protocols.py",
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


def _read_log_tail(base: Path, limit: int = 10) -> str:
    log_file = base / "logs" / "auto_adapt.jsonl"
    if not log_file.is_file():
        return "No auto_adapt logs yet."
    lines = log_file.read_text(encoding="utf-8").strip().splitlines()[-limit:]
    return "\n".join(lines)


def generate_report(output_dir: str | None = None) -> Path:
    root = Path(__file__).resolve().parent.parent
    base = Path(output_dir or os.getenv("PHOENIX_OUTPUT_DIR", "phoenix-output"))
    base.mkdir(parents=True, exist_ok=True)
    passed, output = _run_tests(root)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    chain = FallbackManager.PROTOCOL_CHAIN_AUTO_ADAPT
    chain_rows = "\n".join(f"<li><code>{p}</code></li>" for p in chain)
    log_tail = _read_log_tail(base)

    html = f"""<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
  <meta charset="UTF-8">
  <title>Auto-Adapt Report</title>
  <style>
    body {{ font-family: -apple-system, sans-serif; max-width: 900px; margin: 40px auto; }}
    .ok {{ color: #2e7d32; font-weight: bold; }}
    .bad {{ color: #c62828; font-weight: bold; }}
    pre {{ background: #f5f5f5; padding: 12px; border-radius: 6px; }}
  </style>
</head>
<body>
  <h1>Auto-Adapt Monitoring Report</h1>
  <p>Generated: {now}</p>
  <p>Status: <span class="{'ok' if passed else 'bad'}">{'PASS' if passed else 'FAIL'}</span></p>

  <h2>Protocol Chain</h2>
  <ol>{chain_rows}</ol>

  <h2>Test Output</h2>
  <pre>{output}</pre>

  <h2>Recent Auto-Adapt Log</h2>
  <pre>{log_tail}</pre>
</body>
</html>
"""
    dest = base / "AUTO_ADAPT_REPORT.html"
    dest.write_text(html, encoding="utf-8")
    (base / "auto_adapt_report_summary.json").write_text(
        json.dumps({"generated_at": now, "tests_passed": passed}, indent=2),
        encoding="utf-8",
    )
    return dest


if __name__ == "__main__":
    path = generate_report()
    print(f"Report written to {path}")
