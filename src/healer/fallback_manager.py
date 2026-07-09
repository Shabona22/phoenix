"""Protocol and node fallback manager with DBF-aware priority."""

from __future__ import annotations

from typing import Dict, List, Optional

from orchestrator.node_manager import Node, NodeManager


class FallbackManager:
    PROTOCOL_CHAIN_AUTO_ADAPT = [
        "openvpn_http2",
        "l2tp_websocket",
        "wireguard_http2",
        "openvpn_success",
        "l2tp_success",
        "wireguard_tls",
        "openvpn_obfs4",
        "wireguard_amnezia",
        "l2tp_xray",
        "websocket_plain",
        "tcp_plain",
    ]
    PROTOCOL_CHAIN_DBF = PROTOCOL_CHAIN_AUTO_ADAPT
    PROTOCOL_CHAIN_LEGACY = ["xray", "shadowsocks", "hysteria", "wireguard", "openvpn", "l2tp"]
    CHANNEL_CHAIN = ["standard", "ssh_tunnel", "icmp_tunnel", "doh_tunnel", "mesh_p2p"]
    NO_TLS_PROTOCOLS = ("websocket_plain", "tcp_plain")
    OBFUSCATION_PROTOCOL = "openvpn_obfs4"
    DNS_TUNNEL_CHANNEL = "doh_tunnel"

    def __init__(self, node_manager: NodeManager, dbf_mode: bool = True):
        self.node_manager = node_manager
        self.dbf_mode = dbf_mode
        self._protocol_chain = self.PROTOCOL_CHAIN_DBF if dbf_mode else self.PROTOCOL_CHAIN_LEGACY
        self._protocol_index = 0
        self._channel_index = 0
        self.emergency = False
        self.emergency_mode_active = False
        self.obfuscation_enabled = False
        self.protocols: Dict[str, dict] = {}

    @property
    def protocol_priority(self) -> List[str]:
        return list(self._protocol_chain)

    @property
    def protocol_chain(self) -> List[str]:
        return self._protocol_chain

    @property
    def PROTOCOL_CHAIN(self) -> List[str]:
        """Backward-compatible alias used by legacy tests."""
        return self._protocol_chain

    @property
    def no_tls_index(self) -> int:
        for idx, name in enumerate(self._protocol_chain):
            if name in self.NO_TLS_PROTOCOLS:
                return idx
        return len(self._protocol_chain) - 1

    @property
    def current_protocol(self) -> str:
        return self._protocol_chain[self._protocol_index]

    def get_current_protocol(self) -> str:
        return self.current_protocol

    def switch_protocol(self) -> bool:
        if self._protocol_index < len(self._protocol_chain) - 1:
            self._protocol_index += 1
            return True
        return False

    def register_protocol(self, name: str, config: dict) -> None:
        self.protocols[name] = config

    def switch_to_no_tls(self) -> None:
        self._protocol_index = self.no_tls_index

    def switch_to_dns_tunnel(self) -> None:
        if self.DNS_TUNNEL_CHANNEL in self.CHANNEL_CHAIN:
            self._channel_index = self.CHANNEL_CHAIN.index(self.DNS_TUNNEL_CHANNEL)

    def enable_emergency_mode(self) -> None:
        self.emergency_mode_active = True
        self.emergency_mode()

    def enable_obfuscation(self) -> None:
        self.obfuscation_enabled = True
        if self.OBFUSCATION_PROTOCOL in self._protocol_chain:
            self._protocol_index = self._protocol_chain.index(self.OBFUSCATION_PROTOCOL)

    def switch_node(self) -> bool:
        node = self.node_manager.switch_node()
        return node is not None

    @property
    def current_channel(self) -> str:
        return self.CHANNEL_CHAIN[self._channel_index]

    def switch_channel(self) -> bool:
        if self._channel_index < len(self.CHANNEL_CHAIN) - 1:
            self._channel_index += 1
            return True
        return False

    def emergency_mode(self) -> None:
        self.emergency = True
        self._protocol_index = 0

    def reset(self) -> None:
        self.emergency = False
        self.emergency_mode_active = False
        self.obfuscation_enabled = False
        self._protocol_index = 0
        self._channel_index = 0

    def get_active_node(self) -> Optional[Node]:
        return self.node_manager.select_best_node()
