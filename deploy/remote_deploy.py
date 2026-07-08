#!/usr/bin/env python3
"""Remote SSH deploy to active Phoenix nodes via Doprax credentials."""

from __future__ import annotations

import json
import os
import sys
import time
import zipfile
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from initializer.bootstrap_embedded import BootstrapEmbedded
from orchestrator.api_client import DopraxAPIError, DopraxClient
from orchestrator.config_generator import ConfigGenerator
from orchestrator.node_manager import NodeManager


def _get_paramiko():
    try:
        import paramiko
        return paramiko
    except ImportError:
        raise SystemExit("Install paramiko: pip install paramiko")


def _extract_password(data: Any) -> str:
    if not data:
        return ""
    if isinstance(data, str):
        return data
    if isinstance(data, dict):
        for key in ("password", "root_password", "rootPassword", "passwd", "value"):
            val = data.get(key)
            if val:
                return str(val)
        nested = data.get("data")
        if nested:
            return _extract_password(nested)
    return ""


def _get_password(client: DopraxClient, vm_code: str) -> str:
    env_pwd = os.getenv("PHOENIX_SSH_PASSWORD", "")
    if env_pwd:
        return env_pwd
    for fetcher in (client.get_vm_access, client.get_password):
        try:
            pwd = _extract_password(fetcher(vm_code))
            if pwd:
                return pwd
        except DopraxAPIError:
            continue
    return ""


def _ssh_run(ssh, command: str, password: str, timeout: int = 600) -> tuple[int, str, str]:
    stdin, stdout, stderr = ssh.exec_command(command, get_pty=True, timeout=timeout)
    if "sudo" in command and password:
        time.sleep(0.5)
        stdin.write(password + "\n")
        stdin.flush()
    out = stdout.read().decode(errors="replace")
    err = stderr.read().decode(errors="replace")
    code = stdout.channel.recv_exit_status()
    return code, out, err


def _sftp_put_dir(sftp, local: Path, remote: str) -> None:
    try:
        sftp.mkdir(remote)
    except OSError:
        pass
    for item in local.rglob("*"):
        rel = item.relative_to(local)
        remote_path = f"{remote}/{rel.as_posix()}"
        if item.is_dir():
            try:
                sftp.mkdir(remote_path)
            except OSError:
                pass
        else:
            parent = "/".join(remote_path.split("/")[:-1])
            try:
                sftp.mkdir(parent)
            except OSError:
                pass
            sftp.put(str(item), remote_path)


def deploy_node(node, client: DopraxClient, output_dir: Path) -> str:
    paramiko = _get_paramiko()
    password = _get_password(client, node.vm_code)
    if not password:
        return "FAIL: no password from Doprax API"

    gen = ConfigGenerator(output_dir=str(output_dir))
    configs = gen.generate_for_node(node)
    bundle = BootstrapEmbedded(output_dir=str(output_dir)).create_bundle(configs, node.node_id)

    deploy_dir = ROOT / "deploy"
    remote_base = "/tmp/phoenix-remote"
    bundle_remote = f"{remote_base}/bundle.zip"
    bundle_extract = f"{remote_base}/bundle"

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(
            node.ip,
            username=os.getenv("PHOENIX_SSH_USER", "marj"),
            password=password,
            timeout=30,
            allow_agent=False,
            look_for_keys=False,
        )
        sftp = ssh.open_sftp()
        _ssh_run(ssh, f"rm -rf {remote_base} && mkdir -p {remote_base}/deploy {bundle_extract}", password)
        _sftp_put_dir(sftp, deploy_dir, f"{remote_base}/deploy")
        sftp.put(str(bundle), bundle_remote)
        sftp.close()

        prep = (
            f"cd {remote_base} && unzip -o {bundle_remote} -d {bundle_extract} && "
            f"echo '{password}' | sudo -S env BUNDLE_DIR={bundle_extract} "
            f"DEPLOY_SRC={remote_base}/deploy PHOENIX_DIR=/opt/phoenix "
            f"bash {remote_base}/deploy/bootstrap.sh"
        )
        code, out, err = _ssh_run(ssh, prep, password, timeout=900)
        health_cmd = f"echo '{password}' | sudo -S bash /opt/phoenix/deploy/health_check.sh"
        _, health_out, _ = _ssh_run(ssh, health_cmd, password, timeout=120)
        ssh.close()

        summary = f"exit={code}\n--- bootstrap ---\n{out[-2000:]}\n--- health ---\n{health_out[-1500:]}"
        if err:
            summary += f"\n--- stderr ---\n{err[-500:]}"
        return summary
    except Exception as exc:
        return f"FAIL: {exc}"


def main() -> int:
    output_dir = Path(os.getenv("PHOENIX_OUTPUT_DIR", "phoenix-output"))
    try:
        client = DopraxClient()
        mgr = NodeManager(client)
        mgr.refresh()
        nodes = mgr.list_nodes()
    except DopraxAPIError as exc:
        print(f"API error: {exc}")
        return 1

    if not nodes:
        print("No active nodes (DE/FR excluded)")
        return 1

    results: dict[str, str] = {}
    for node in nodes:
        if not node.ip:
            mgr.enrich_node_ips(node)
        if not node.ip:
            results[node.vm_code] = "SKIP: no IP"
            continue
        print(f"Deploying to {node.name} ({node.ip})...")
        results[node.vm_code] = deploy_node(node, client, output_dir)
        print(results[node.vm_code][:300])

    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "deploy_results.json").write_text(json.dumps(results, indent=2))
    print(f"Results saved to {output_dir / 'deploy_results.json'}")

    from completion_report import generate_report
    generate_report(str(output_dir))
    return 0 if all(not v.startswith("FAIL") for v in results.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
