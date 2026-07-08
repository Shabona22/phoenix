"""Node lifecycle management for Doprax VMs."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from orchestrator.api_client import DopraxClient


@dataclass
class Node:
    vm_code: str
    name: str
    ip: str = ""
    status: str = "unknown"
    traffic_used: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def node_id(self) -> str:
        return self.vm_code


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
                    metadata=vm,
                )
            )
        self._nodes = nodes
        return nodes

    def list_nodes(self) -> List[Node]:
        if not self._nodes:
            return self.refresh()
        return self._nodes

    def get_node(self, vm_code: str) -> Optional[Node]:
        for node in self.list_nodes():
            if node.vm_code == vm_code:
                return node
        return None

    def select_best_node(self) -> Optional[Node]:
        nodes = [n for n in self.list_nodes() if n.status in ("running", "active", "online", "unknown")]
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
        vm_code = result.get("vmCode") or result.get("id") or result.get("code", "")
        node = Node(
            vm_code=vm_code,
            name=result.get("sysName", vm_code),
            ip=result.get("ip", ""),
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
