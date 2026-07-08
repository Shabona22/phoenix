"""Node lifecycle management for Doprax VMs."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from orchestrator.api_client import DopraxClient

DEFAULT_EXCLUDED_LOCATIONS = {"germany", "de", "france", "fr", "paris", "frankfurt", "berlin"}


def _parse_excluded_locations() -> set[str]:
    raw = os.getenv("PHOENIX_EXCLUDED_LOCATIONS", "")
    if raw:
        return {part.strip().lower() for part in raw.split(",") if part.strip()}
    return DEFAULT_EXCLUDED_LOCATIONS


def is_excluded_location(country: str = "", location_name: str = "") -> bool:
    haystack = f"{country} {location_name}".lower()
    return any(token in haystack for token in _parse_excluded_locations())


@dataclass
class Node:
    vm_code: str
    name: str
    ip: str = ""
    status: str = "unknown"
    traffic_used: float = 0.0
    country: str = ""
    location_name: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def node_id(self) -> str:
        return self.vm_code

    @property
    def is_excluded(self) -> bool:
        return is_excluded_location(self.country, self.location_name)


class NodeManager:
    def __init__(self, client: Optional[DopraxClient] = None):
        self.client = client or DopraxClient()
        self._nodes: List[Node] = []
        self._current_index = 0

    def refresh(self) -> List[Node]:
        vms = self.client.list_vms()
        nodes: List[Node] = []
        for vm in vms:
            vm_code = vm.get("vmCode") or vm.get("id") or vm.get("code", "")
            name = vm.get("sysName") or vm.get("name", vm_code)
            ip = vm.get("ipv4") or vm.get("ip") or ""
            ips = vm.get("ips") or []
            if not ip and ips:
                ip = ips[0].get("address") or ips[0].get("ip", "") if isinstance(ips[0], dict) else str(ips[0])
            nodes.append(
                Node(
                    vm_code=vm_code,
                    name=name,
                    ip=ip,
                    status=vm.get("status", "unknown"),
                    traffic_used=float(vm.get("trafficUsed", 0) or 0),
                    country=str(vm.get("country", "") or ""),
                    location_name=str(vm.get("locationName", "") or ""),
                    metadata=vm,
                )
            )
        self._nodes = nodes
        return nodes

    def list_nodes(self, *, include_excluded: bool = False) -> List[Node]:
        if not self._nodes:
            self.refresh()
        if include_excluded:
            return self._nodes
        return [n for n in self._nodes if not n.is_excluded]

    def list_all_nodes(self) -> List[Node]:
        return self.list_nodes(include_excluded=True)

    def get_node(self, vm_code: str) -> Optional[Node]:
        for node in self.list_nodes():
            if node.vm_code == vm_code:
                return node
        return None

    def select_best_node(self) -> Optional[Node]:
        nodes = [
            n
            for n in self.list_nodes()
            if n.status in ("running", "active", "online", "unknown")
        ]
        if not nodes:
            return None
        return min(nodes, key=lambda n: n.traffic_used)

    def switch_node(self) -> Optional[Node]:
        nodes = self.list_nodes()
        if not nodes:
            return None
        self._current_index = (self._current_index + 1) % len(nodes)
        return nodes[self._current_index]

    def provision_node(self, payload: Dict[str, Any]) -> Node:
        result = self.client.create_vm(payload)
        vm_code = (
            result.get("vmCode")
            or result.get("vm_code")
            or (result.get("metadata") or {}).get("vm_code")
            or result.get("service_id")
            or result.get("id")
            or result.get("code", "")
        )
        node = Node(
            vm_code=vm_code,
            name=result.get("name") or result.get("sysName", vm_code),
            ip=result.get("ip") or result.get("ipv4", ""),
            status=result.get("status", "provisioning"),
            metadata=result,
        )
        self._nodes.append(node)
        return node

    def enrich_node_ips(self, node: Node) -> Node:
        if node.ip:
            return node
        try:
            detail = self.client.get_vm(node.vm_code)
            node.ip = detail.get("ipv4") or detail.get("ip") or node.ip
            if not node.ip:
                ips = self.client.get_ips(node.vm_code)
                if ips:
                    v4 = next((i for i in ips if i.get("version") == 4), ips[0])
                    node.ip = v4.get("address") or v4.get("ip", node.ip)
        except Exception:
            pass
        return node
