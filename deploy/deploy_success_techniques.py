#!/usr/bin/env python3
"""Remote deploy of success-technique configs to active Phoenix nodes."""

from __future__ import annotations

import json
import os
import sys
import tarfile
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from deploy.remote_deploy import _get_credentials, _ssh_run_subprocess  # noqa: E402
from orchestrator.api_client import DopraxClient  # noqa: E402
from orchestrator.node_manager import NodeManager  # noqa: E402

SUCCESS_PROTOCOLS = (
    "openvpn_success",
    "l2tp_success",
    "wireguard_tls",
)


def _build_archive(node_id: str, output_dir: Path) -> Path:
    tmp = Path(tempfile.mkdtemp(prefix="phoenix-success-"))
    staging = tmp / "configs"
    for proto in SUCCESS_PROTOCOLS:
        src = output_dir / "configs" / proto / node_id
        if src.is_dir():
            dest = staging / proto / node_id
            dest.parent.mkdir(parents=True, exist_ok=True)
            for item in src.iterdir():
                if item.is_file():
                    dest.mkdir(parents=True, exist_ok=True)
                    dest.joinpath(item.name).write_bytes(item.read_bytes())
    archive = tmp / "success-configs.tar.gz"
    with tarfile.open(archive, "w:gz") as tar:
        tar.add(staging, arcname="configs")
    return archive


def deploy_node(node, client: DopraxClient, output_dir: Path) -> str:
    username, password = _get_credentials(client, node.vm_code)
    if not password:
        return "FAIL: no SSH password"

    archive = _build_archive(node.node_id, output_dir)
    remote_archive = "/tmp/phoenix-success-configs.tar.gz"

    try:
        from deploy.remote_deploy import _upload_file_subprocess

        _upload_file_subprocess(archive, remote_archive, node.ip, username, password)

        prep = (
            f"sudo -S mkdir -p /opt/phoenix/configs && "
            f"sudo -S tar -xzf {remote_archive} -C /opt/phoenix --strip-components=0 && "
            f"for p in openvpn_success l2tp_success wireguard_tls; do "
            f"if [ -d /opt/phoenix/configs/$p/{node.node_id} ]; then "
            f"sudo -S mkdir -p /opt/phoenix/configs/$p && "
            f"sudo -S cp -a /opt/phoenix/configs/$p/{node.node_id}/. /opt/phoenix/configs/$p/; "
            f"fi; done"
        )
        code, out, err = _ssh_run_subprocess(node.ip, username, password, prep, timeout=120)

        script_local = ROOT / "deploy" / "setup_success_techniques.sh"
        script_remote = "/tmp/setup_success_techniques.sh"
        _upload_file_subprocess(script_local, script_remote, node.ip, username, password)
        run = (
            f"chmod +x {script_remote} && "
            f"sudo -S env PHOENIX_DIR=/opt/phoenix bash {script_remote}"
        )
        code2, out2, err2 = _ssh_run_subprocess(node.ip, username, password, run, timeout=600)
        health = (
            "sudo -S ss -lntp | egrep '(:443 |:5443 |:1701|:4500)' ; "
            "sudo -S ss -lunp | egrep '(:1701|:4500|:51820|:[0-9]{4,5})' ; "
            "sudo -S systemctl is-active openvpn-server@server-success stunnel4 strongswan-starter xl2tpd 2>/dev/null || true"
        )
        _, hout, herr = _ssh_run_subprocess(node.ip, username, password, health, timeout=60)
        return (
            f"prep_exit={code} setup_exit={code2}\n"
            f"--- setup ---\n{out2[-2500:]}\n"
            f"--- health ---\n{hout}\n{herr[-400:]}"
        )
    except Exception as exc:
        return f"FAIL: {exc}"
    finally:
        import shutil

        shutil.rmtree(archive.parent, ignore_errors=True)


def main() -> int:
    output_dir = Path(os.getenv("PHOENIX_OUTPUT_DIR", "phoenix-output"))
    client = DopraxClient()
    mgr = NodeManager(client)
    mgr.refresh()
    nodes = [n for n in mgr.list_nodes() if n.ip]
    if not nodes:
        print("No active nodes")
        return 1

    results: dict[str, str] = {}
    for node in nodes:
        print(f"Deploying success techniques -> {node.name} ({node.ip})")
        results[node.vm_code] = deploy_node(node, client, output_dir)
        print(results[node.vm_code][:500])

    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "success_deploy_results.json").write_text(
        json.dumps(results, indent=2), encoding="utf-8"
    )
    print(f"Saved {output_dir / 'success_deploy_results.json'}")
    return 0 if all(not v.startswith("FAIL") for v in results.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
