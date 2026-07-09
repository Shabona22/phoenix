#!/usr/bin/env python3
"""CLI wrapper for MikroTik API deployment."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from mikrotik.deploy_winbox import deploy_via_api


def main() -> int:
    parser = argparse.ArgumentParser(description="Deploy Phoenix MikroTik scripts via RouterOS API")
    parser.add_argument("--ip", required=True, help="MikroTik IP address")
    parser.add_argument("--username", required=True, help="MikroTik username")
    parser.add_argument("--password", required=True, help="MikroTik password")
    parser.add_argument("--port", type=int, default=8728, help="RouterOS API port")
    args = parser.parse_args()

    print("Starting MikroTik deployment via RouterOS API...")
    results = deploy_via_api(args.ip, args.username, args.password, port=args.port)
    print(json.dumps(results, indent=2))

    failed = [name for name, info in results.items() if not info.get("uploaded")]
    if failed:
        print(f"Failed scripts: {', '.join(failed)}")
        return 1
    print("Deployment completed successfully!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
