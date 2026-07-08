"""Protocol and node fallback manager."""

from __future__ import annotations

from typing import List, Optional

from orchestrator.node_manager import Node, NodeManager


class FallbackManager:
    PROTOCOL_CHAIN = ["xray", "shadowsocks", "hysteria", "wireguard", "openvpn", "l2tp"]

    def __init__(self, node_manager: NodeManager):
        self.node_manager = node_manager
        self._protocol_index = 0
        self.emergency = False

    @property
    def current_protocol(self) -> str:
        return self.PROTOCOL_CHAIN[self._protocol_index]

    def switch_protocol(self) -> bool:
        if self._protocol_index < len(self.PROTOCOL_CHAIN) - 1:
            self._protocol_index += 1
            return True
        return False

    def switch_node(self) -> bool:
        node = self.node_manager.switch_node()
        return node is not None

    def emergency_mode(self) -> None:
        self.emergency = True
        self._protocol_index = 0

    def reset(self) -> None:
        self.emergency = False
        self._protocol_index = 0

    def get_active_node(self) -> Optional[Node]:
        return self.node_manager.select_best_node()
