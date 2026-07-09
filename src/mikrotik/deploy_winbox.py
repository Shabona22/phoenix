#!/usr/bin/env python3
"""Deploy Phoenix MikroTik scripts via RouterOS API."""

from __future__ import annotations

import time
from typing import Any, Dict, Optional

from mikrotik.advanced_config_generator import MikroTikConfigGenerator, SCRIPT_ORDER
from mikrotik.winbox_connector import WinBoxConnector


def deploy_via_api(
    ip: str,
    username: str,
    password: str,
    port: int = 8728,
    connector: Optional[WinBoxConnector] = None,
) -> Dict[str, Dict[str, Any]]:
    generator = MikroTikConfigGenerator()
    scripts = generator.generate_all_scripts()
    client = connector or WinBoxConnector(ip, username, password, port=port)
    owns_connector = connector is None
    results: Dict[str, Dict[str, Any]] = {}

    if not client.connect():
        if owns_connector:
            client.close()
        return {name: {"uploaded": False, "run": False, "error": "connection failed"} for name in SCRIPT_ORDER}

    try:
        for name in SCRIPT_ORDER:
            content = scripts.get(name, "")
            entry: Dict[str, Any] = {"uploaded": False, "run": False, "error": None}
            try:
                entry["uploaded"] = client.upload_script(name, content)
                if entry["uploaded"]:
                    time.sleep(0.5)
                    run_result = client.run_script(name)
                    entry["run"] = "error" not in str(run_result).lower()
                    entry["result"] = run_result
                else:
                    entry["error"] = "upload failed"
            except Exception as exc:  # noqa: BLE001
                entry["error"] = str(exc)
            results[name] = entry
            time.sleep(0.5)
    finally:
        if owns_connector:
            client.close()

    return results
