#!/usr/bin/env python3
"""Phoenix VPN V10 CLI entry point."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from healer.fallback_manager import FallbackManager
from healer.heartbeat import Heartbeat
from initializer.bootstrap_embedded import BootstrapEmbedded
from orchestrator.api_client import DopraxAPIError, DopraxClient
from orchestrator.config_generator import ConfigGenerator
from orchestrator.node_manager import NodeManager
from orchestrator.subscription_manager import SubscriptionManager
from utils.log_manager import LogManager


def cmd_adapt(args: argparse.Namespace) -> int:
    from monitoring.auto_adapt import AutoAdapt

    log = LogManager()
    mgr = NodeManager()
    fallback = FallbackManager(mgr)
    adapt = AutoAdapt(fallback, interval=args.interval)

    if args.daemon:
        adapt.start()
        log.info(f"Auto-Adapt daemon started (interval={args.interval}s)")
        try:
            while True:
                import time

                time.sleep(3600)
        except KeyboardInterrupt:
            adapt.stop()
            log.info("Auto-Adapt stopped")
        return 0

    status = adapt.run_once()
    print(json.dumps(status, indent=2))
    log.info(
        f"level={status.get('level')} recommendation={status.get('recommendation')} "
        f"protocol={fallback.current_protocol}"
    )
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    log = LogManager()
    try:
        client = DopraxClient()
        mgr = NodeManager(client)
        nodes = mgr.list_all_nodes()
        log.info(f"Found {len(nodes)} nodes ({len(mgr.list_nodes())} active, excluding DE/FR)")
        for node in nodes:
            flag = " [EXCLUDED]" if node.is_excluded else ""
            print(
                f"  {node.name} ({node.vm_code}) ip={node.ip} "
                f"loc={node.country}/{node.location_name} status={node.status}{flag}"
            )
        return 0
    except DopraxAPIError as exc:
        log.error(str(exc))
        return 1


def cmd_generate(args: argparse.Namespace) -> int:
    log = LogManager()
    mgr = NodeManager()
    mgr.refresh()
    nodes = mgr.list_nodes()
    if not nodes:
        log.error("No eligible nodes found (Germany/France excluded)")
        return 1

    gen = ConfigGenerator()
    sub = SubscriptionManager()
    all_configs = {}
    for node in nodes:
        if not node.ip:
            mgr.enrich_node_ips(node)
        if node.ip:
            configs = gen.generate_for_node(node)
            all_configs[node.node_id] = configs
            log.info(f"Generated configs for {node.name}")

    sub.export_all(all_configs)
    log.info(f"Exported subscriptions for {len(all_configs)} nodes")
    return 0


def cmd_provision(args: argparse.Namespace) -> int:
    log = LogManager()
    client = DopraxClient()
    mgr = NodeManager(client)

    if not args.product_version_id:
        log.error("product_version_id is required (use Doprax catalogue)")
        return 1
    if not args.location:
        log.error("location code is required (e.g. gcore_50, vultr_waw)")
        return 1

    payload = {
        "product_version_id": args.product_version_id,
        "name": args.name,
        "selections": {
            "location": {"code": args.location},
            "operating_system": {"code": args.os},
        },
    }

    try:
        result = mgr.provision_node(payload)
        log.info(f"Provisioned service status={result.status} vm_code={result.vm_code or 'pending'}")
        print(json.dumps({"vm_code": result.vm_code, "status": result.status, "service": result.metadata}, indent=2))
        return 0
    except DopraxAPIError as exc:
        log.error(f"Provision failed: {exc}")
        return 1


def cmd_deploy(args: argparse.Namespace) -> int:
    log = LogManager()
    mgr = NodeManager()
    mgr.refresh()
    nodes = mgr.list_nodes()
    if not nodes:
        log.error("No eligible nodes to deploy (Germany/France excluded)")
        return 1

    gen = ConfigGenerator()
    bootstrap = BootstrapEmbedded()
    for node in nodes:
        if not node.ip:
            mgr.enrich_node_ips(node)
        if node.ip:
            configs = gen.generate_for_node(node)
            bootstrap.create_bundle(configs, node.node_id)
            log.info(f"Deploy bundle ready for {node.name} ({node.ip})")

    log.info("Deploy bundles created in phoenix-output/bootstrap/")
    log.info("Copy deploy/ to server and run bootstrap.sh")
    return 0


def cmd_mikrotik(args: argparse.Namespace) -> int:
    from mikrotik.advanced_config_generator import MikroTikConfigGenerator
    from mikrotik_deployment_report import generate_report

    log = LogManager()
    if args.report:
        path = generate_report()
        print(path)
        log.info(f"MikroTik report: {path}")
        return 0

    if args.deploy_ssh:
        if not args.ip:
            print("ERROR: --ip required for --ssh deploy")
            return 1
        import subprocess

        root = Path(__file__).resolve().parent.parent
        cmd = [str(root / "deploy" / "mikrotik_deploy.sh"), "--ip", args.ip]
        if args.user:
            cmd.extend(["--user", args.user])
        if args.password:
            cmd.extend(["--password", args.password])
        result = subprocess.run(cmd, cwd=root)
        return result.returncode

    generator = MikroTikConfigGenerator()
    scripts = generator.generate_all_scripts()
    print(json.dumps(list(scripts.keys()), indent=2))
    log.info(f"Generated {len(scripts)} MikroTik scripts")
    return 0


def cmd_heal(args: argparse.Namespace) -> int:
    log = LogManager()
    mgr = NodeManager()
    fallback = FallbackManager(mgr)
    hb = Heartbeat(on_failure=lambda: fallback.switch_protocol())
    if hb.ping():
        log.info("Heartbeat OK")
        return 0
    log.warning("Heartbeat failed, attempting fallback")
    if fallback.switch_protocol():
        log.info(f"Switched to protocol: {fallback.current_protocol}")
        return 0
    if fallback.switch_node():
        log.info("Switched node")
        return 0
    fallback.emergency_mode()
    log.error("Emergency mode activated")
    return 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Phoenix VPN V10")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("status", help="List Doprax VMs").set_defaults(func=cmd_status)
    sub.add_parser("generate", help="Generate configs for all nodes").set_defaults(func=cmd_generate)

    p_prov = sub.add_parser("provision", help="Provision new VM via Doprax v2 API")
    p_prov.add_argument("--name", default="phoenix-node")
    p_prov.add_argument("--product-version-id", dest="product_version_id", required=False)
    p_prov.add_argument("--location", default="", help="Location code from catalogue")
    p_prov.add_argument("--os", default="ubuntu_22_04")
    p_prov.set_defaults(func=cmd_provision)

    sub.add_parser("deploy", help="Prepare deploy bundles").set_defaults(func=cmd_deploy)
    sub.add_parser("heal", help="Run healing check").set_defaults(func=cmd_heal)

    p_adapt = sub.add_parser("adapt", help="Run Auto-Adapt monitoring loop")
    p_adapt.add_argument("--once", action="store_true", help="Run one adaptation cycle")
    p_adapt.add_argument("--daemon", action="store_true", help="Run continuous adaptation")
    p_adapt.add_argument("--interval", type=int, default=60, help="Seconds between cycles")
    p_adapt.set_defaults(func=cmd_adapt)

    p_mikrotik = sub.add_parser("mikrotik", help="MikroTik hap ax3 scripts and deploy")
    p_mikrotik.add_argument("action", nargs="?", default="generate", choices=["generate", "deploy", "report"])
    p_mikrotik.add_argument("--ssh", dest="deploy_ssh", action="store_true", help="Deploy via SSH")
    p_mikrotik.add_argument("--ip", default="", help="MikroTik IP")
    p_mikrotik.add_argument("--user", default="admin", help="SSH/API username")
    p_mikrotik.add_argument("--password", default="", help="SSH/API password")
    p_mikrotik.add_argument("--report", action="store_true", help="Generate HTML report")

    def _mikrotik_dispatch(args: argparse.Namespace) -> int:
        if args.action == "report" or args.report:
            args.report = True
        if args.action == "deploy":
            args.deploy_ssh = True
        return cmd_mikrotik(args)

    p_mikrotik.set_defaults(func=_mikrotik_dispatch)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return 0
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
