"""Generate MIKROTIK_DEPLOYMENT_REPORT.html."""

from __future__ import annotations

import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from mikrotik.advanced_config_generator import MikroTikConfigGenerator, MikroTikSettings, SCRIPT_ORDER


def _run_tests(root: Path) -> tuple[bool, str]:
    result = subprocess.run(
        [
            "python3",
            "-m",
            "pytest",
            "tests/unit/test_mikrotik_config_generator.py",
            "tests/unit/test_mikrotik_usb_manager.py",
            "tests/unit/test_mikrotik_winbox_connector.py",
            "tests/unit/test_mikrotik_deploy.py",
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


def _redact_settings(settings: MikroTikSettings) -> dict:
    data = {
        "wan1_gateway": settings.wan1_gateway,
        "wan2_gateway": settings.wan2_gateway,
        "syslog_host": settings.syslog_host,
        "mesh_ssid": settings.mesh_ssid,
        "hap_model": settings.hap_model,
        "wg_private_key": "***" if settings.wg_private_key else "(not set)",
        "wg_public_key": "***" if settings.wg_public_key else "(not set)",
        "l2tp_psk": "***" if settings.l2tp_psk else "(not set)",
    }
    return data


def generate_report(output_dir: str | None = None) -> Path:
    root = Path(__file__).resolve().parent.parent
    base = Path(output_dir or os.getenv("PHOENIX_OUTPUT_DIR", "phoenix-output"))
    base.mkdir(parents=True, exist_ok=True)

    generator = MikroTikConfigGenerator(root=root)
    generator.generate_all_scripts()
    passed, test_output = _run_tests(root)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    script_rows = ""
    for path in sorted(generator.list_script_paths()):
        script_rows += f"<tr><td><code>{path.name}</code></td><td>{path.stat().st_size} bytes</td></tr>\n"

    order_rows = "\n".join(f"<li><code>{name}.rsc</code></li>" for name in SCRIPT_ORDER)
    settings = _redact_settings(generator.settings)
    settings_rows = "\n".join(
        f"<tr><td><code>{k}</code></td><td>{v}</td></tr>" for k, v in settings.items()
    )

    html = f"""<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
  <meta charset="UTF-8">
  <title>MikroTik Deployment Report</title>
  <style>
    body {{ font-family: -apple-system, sans-serif; max-width: 900px; margin: 40px auto; }}
    .ok {{ color: #2e7d32; font-weight: bold; }}
    .bad {{ color: #c62828; font-weight: bold; }}
    table {{ border-collapse: collapse; width: 100%; margin: 16px 0; }}
    th, td {{ border: 1px solid #ddd; padding: 8px; text-align: right; }}
    th {{ background: #f5f5f5; }}
    pre {{ background: #f5f5f5; padding: 12px; border-radius: 6px; }}
    code {{ background: #f5f5f5; padding: 2px 6px; border-radius: 4px; }}
  </style>
</head>
<body>
  <h1>Phoenix V10 – MikroTik Deployment Report</h1>
  <p>Generated: {now}</p>
  <p>Status: <span class="{'ok' if passed else 'bad'}">{'PASS' if passed else 'FAIL'}</span></p>

  <h2>Deploy Order</h2>
  <ol>{order_rows}</ol>

  <h2>Generated Scripts</h2>
  <table>
    <tr><th>Script</th><th>Size</th></tr>
    {script_rows}
  </table>

  <h2>Settings (redacted)</h2>
  <table>
    <tr><th>Key</th><th>Value</th></tr>
    {settings_rows}
  </table>

  <h2>Deploy Commands</h2>
  <pre>./deploy/mikrotik_deploy.sh --generate-only
./deploy/mikrotik_deploy.sh --ip 192.168.88.1 --user admin --password '...'
PYTHONPATH=src python3 deploy/mikrotik_deploy_winbox.py --ip 192.168.88.1 --username admin --password '...'</pre>

  <h2>Test Output</h2>
  <pre>{test_output}</pre>
</body>
</html>
"""
    out_path = base / "MIKROTIK_DEPLOYMENT_REPORT.html"
    out_path.write_text(html, encoding="utf-8")
    return out_path


if __name__ == "__main__":
    path = generate_report()
    print(f"Report written to {path}")
