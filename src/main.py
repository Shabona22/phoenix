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


def cmd_status(args: argparse.Namespace) -> int:
    log = LogManager()
    try:
        client = DopraxClient()
        mgr = NodeManager(client)
        nodes = mgr.refresh()
        log.info(f"Found {len(nodes)} nodes")
        for node in nodes:
            print(f"  {node.name} ({node.vm_code}) ip={node.ip} status={node.status}")
        return 0
    except DopraxAPIError as exc:
        log.error(str(exc))
        return 1


def cmd_generate(args: argparse.Namespace) -> int:
    log = LogManager()
    mgr = NodeManager()
    nodes = mgr.refresh()
    if not nodes:
        log.error("No nodes found")
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

    payload = {
        "name": args.name,
        "provider": args.provider,
        "location": args.location,
        "plan": args.plan,
        "os": args.os,
    }
    payload = {k: v for k, v in payload.items() if v}

    try:
        node = mgr.provision_node(payload)
        log.info(f"Provisioned node {node.vm_code} status={node.status}")
        print(json.dumps({"vm_code": node.vm_code, "status": node.status}, indent=2))
        return 0
    except DopraxAPIError as exc:
        log.error(f"Provision failed: {exc}")
        return 1


def cmd_deploy(args: argparse.Namespace) -> int:
    log = LogManager()
    mgr = NodeManager()
    nodes = mgr.refresh()
    if not nodes:
        log.error("No nodes to deploy")
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

    p_prov = sub.add_parser("provision", help="Provision new VM via Doprax API")
    p_prov.add_argument("--name", default="phoenix-node")
    p_prov.add_argument("--provider", default="")
    p_prov.add_argument("--location", default="")
    p_prov.add_argument("--plan", default="")
    p_prov.add_argument("--os", default="ubuntu-22.04")
    p_prov.set_defaults(func=cmd_provision)

    sub.add_parser("deploy", help="Prepare deploy bundles").set_defaults(func=cmd_deploy)
    sub.add_parser("heal", help="Run healing check").set_defaults(func=cmd_heal)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return 0
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
