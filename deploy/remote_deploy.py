#!/usr/bin/env python3
"""Remote SSH deploy to active Phoenix nodes via Doprax credentials."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
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
        for key in ("tempPass", "password", "root_password", "rootPassword", "passwd", "value"):
            val = data.get(key)
            if val:
                return str(val)
        nested = data.get("data")
        if nested:
            return _extract_password(nested)
    return ""


def _extract_username(data: Any, fallback: str) -> str:
    if isinstance(data, dict):
        for key in ("vmUsername", "username", "user"):
            val = data.get(key)
            if val:
                return str(val)
        nested = data.get("data")
        if isinstance(nested, dict):
            return _extract_username(nested, fallback)
    return fallback


def _get_credentials(client: DopraxClient, vm_code: str) -> tuple[str, str]:
    env_pwd = os.getenv("PHOENIX_SSH_PASSWORD", "")
    env_user = os.getenv("PHOENIX_SSH_USER", "")
    if env_pwd:
        return env_user or "root", env_pwd

    for fetcher in (client.get_vm_access, client.get_password):
        try:
            data = fetcher(vm_code)
            pwd = _extract_password(data)
            if pwd:
                user = _extract_username(data, env_user or "root")
                return user, pwd
        except DopraxAPIError:
            continue
    return env_user or "root", ""


def _upload_file_subprocess(local_path: Path, remote_path: str, host: str, username: str, password: str) -> None:
    target = f"{username}@{host}:{remote_path}"
    if shutil.which("sshpass"):
        result = subprocess.run(
            [
                "sshpass", "-p", password,
                "scp", "-o", "StrictHostKeyChecking=no",
                "-o", "UserKnownHostsFile=/dev/null",
                str(local_path), target,
            ],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr or result.stdout or "scp failed")
        return
    raise RuntimeError("sshpass not installed; install with: brew install sshpass")


def _upload_file(ssh, local_path: Path, remote_path: str) -> None:
    size = local_path.stat().st_size
    stdin, stdout, stderr = ssh.exec_command(f"cat > {remote_path}")
    with open(local_path, "rb") as handle:
        while True:
            chunk = handle.read(65536)
            if not chunk:
                break
            stdin.write(chunk)
    stdin.channel.shutdown_write()
    exit_code = stdout.channel.recv_exit_status()
    if exit_code != 0:
        raise RuntimeError(f"upload failed: {stderr.read().decode(errors='replace')}")
    _, out, _ = ssh.exec_command(f"wc -c < {remote_path}")
    remote_size = int(out.read().decode().strip() or "0")
    if remote_size != size:
        raise RuntimeError(f"upload size mismatch local={size} remote={remote_size}")


def _ssh_run_subprocess(host: str, username: str, password: str, command: str, timeout: int = 900) -> tuple[int, str, str]:
    remote_cmd = command
    if "sudo -S" in command:
        remote_cmd = command.replace("sudo -S", f"echo '{password}' | sudo -S", 1)
    result = subprocess.run(
        [
            "sshpass", "-p", password,
            "ssh", "-o", "StrictHostKeyChecking=no",
            "-o", "UserKnownHostsFile=/dev/null",
            f"{username}@{host}",
            remote_cmd,
        ],
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    return result.returncode, result.stdout, result.stderr


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


def _build_deploy_archive(bundle_path: Path, deploy_dir: Path) -> Path:
    tmp = Path(tempfile.mkdtemp(prefix="phoenix-deploy-"))
    staging = tmp / "staging"
    shutil.copytree(deploy_dir, staging / "deploy")
    bundle_extract = staging / "bundle"
    bundle_extract.mkdir()
    import zipfile

    with zipfile.ZipFile(bundle_path, "r") as zf:
        zf.extractall(bundle_extract)

    archive = tmp / "phoenix-deploy.tar.gz"
    with tarfile.open(archive, "w:gz") as tar:
        tar.add(staging, arcname="phoenix-remote")
    return archive


def deploy_node(node, client: DopraxClient, output_dir: Path) -> str:
    paramiko = _get_paramiko()
    username, password = _get_credentials(client, node.vm_code)
    if not password:
        return "FAIL: no password from Doprax API"

    gen = ConfigGenerator(output_dir=str(output_dir))
    configs = gen.generate_for_node(node)
    bundle = BootstrapEmbedded(output_dir=str(output_dir)).create_bundle(configs, node.node_id)
    archive = _build_deploy_archive(bundle, ROOT / "deploy")

    remote_base = "/tmp/phoenix-remote"
    remote_archive = f"{remote_base}.tar.gz"

    def connect():
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(
            node.ip,
            username=username,
            password=password,
            timeout=30,
            allow_agent=False,
            look_for_keys=False,
            banner_timeout=30,
        )
        transport = ssh.get_transport()
        if transport:
            transport.set_keepalive(30)
        return ssh

    try:
        _upload_file_subprocess(archive, remote_archive, node.ip, username, password)

        prep = (
            f"rm -rf {remote_base} && mkdir -p {remote_base} && "
            f"tar -xzf {remote_archive} -C {remote_base} --strip-components=1 && "
            f"sudo -S env BUNDLE_DIR={remote_base}/bundle "
            f"DEPLOY_SRC={remote_base}/deploy PHOENIX_DIR=/opt/phoenix "
            f"bash {remote_base}/deploy/bootstrap.sh"
        )
        code, out, err = _ssh_run_subprocess(node.ip, username, password, prep, timeout=900)
        _, health_out, health_err = _ssh_run_subprocess(
            node.ip, username, password, "sudo -S bash /opt/phoenix/deploy/health_check.sh", timeout=120
        )

        summary = f"user={username} exit={code}\n--- bootstrap ---\n{out[-3000:]}\n--- health ---\n{health_out[-1500:]}"
        if err:
            summary += f"\n--- stderr ---\n{err[-800:]}"
        if health_err:
            summary += f"\n--- health stderr ---\n{health_err[-400:]}"
        return summary
    except Exception as exc:
        import traceback
        return f"FAIL: {exc}\n{traceback.format_exc()[-1000:]}"
    finally:
        shutil.rmtree(archive.parent, ignore_errors=True)


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
        print(results[node.vm_code][:400])

    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "deploy_results.json").write_text(json.dumps(results, indent=2))
    print(f"Results saved to {output_dir / 'deploy_results.json'}")

    from completion_report import generate_report
    generate_report(str(output_dir))
    return 0 if all(not v.startswith("FAIL") for v in results.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
