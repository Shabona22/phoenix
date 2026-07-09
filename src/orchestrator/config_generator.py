"""Multi-protocol config generator."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from orchestrator.node_manager import Node
from protocols.hysteria_config import HysteriaConfig
from protocols.l2tp_config import L2TPConfig
from protocols.l2tp_xray_tunnel import L2TPXrayTunnelConfig
from protocols.no_tls.http_upgrade import HTTPUpgradeConfig
from protocols.no_tls.tcp_plain import TCPPlainConfig
from protocols.no_tls.websocket_plain import WebSocketPlainConfig
from protocols.openvpn_cloak import OpenVPNCloakConfig
from protocols.openvpn_obfs4 import OpenVPNObfs4Config
from protocols.openvpn_config import OpenVPNConfig
from protocols.openvpn_success import OpenVPNSuccessConfig
from protocols.shadowsocks_config import ShadowsocksConfig
from protocols.wireguard_amnezia import WireGuardAmneziaConfig
from protocols.wireguard_config import WireGuardConfig
from protocols.wireguard_tls import WireGuardTLSConfig
from protocols.xray_config import XrayConfig
from protocols.xray_reality import XrayRealityConfig
from protocols.l2tp_success import L2TPSuccessConfig
from protocols.l2tp_websocket import L2TPWebSocketConfig
from protocols.openvpn_http2 import OpenVPNHttp2Config
from protocols.wireguard_http2 import WireGuardHttp2Config


class ConfigGenerator:
    PROTOCOLS = {
        "openvpn_http2": OpenVPNHttp2Config,
        "l2tp_websocket": L2TPWebSocketConfig,
        "wireguard_http2": WireGuardHttp2Config,
        "openvpn_success": OpenVPNSuccessConfig,
        "l2tp_success": L2TPSuccessConfig,
        "wireguard_tls": WireGuardTLSConfig,
        "openvpn_obfs4": OpenVPNObfs4Config,
        "websocket_plain": WebSocketPlainConfig,
        "tcp_plain": TCPPlainConfig,
        "http_upgrade": HTTPUpgradeConfig,
        "openvpn_cloak": OpenVPNCloakConfig,
        "wireguard_amnezia": WireGuardAmneziaConfig,
        "l2tp_xray": L2TPXrayTunnelConfig,
        "xray_reality": XrayRealityConfig,
        "openvpn": OpenVPNConfig,
        "l2tp": L2TPConfig,
        "xray": XrayConfig,
        "shadowsocks": ShadowsocksConfig,
        "wireguard": WireGuardConfig,
        "hysteria": HysteriaConfig,
    }

    DBF_PRIORITY = [
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
        "http_upgrade",
    ]

    SERVER_FILES: Dict[str, Tuple[str, str]] = {
        "xray": ("config.json", "json"),
        "shadowsocks": ("config.json", "json"),
        "hysteria": ("config.yaml", "yaml"),
        "wireguard": ("wg0.conf", "conf"),
        "wireguard_tls": ("wg_tls.conf", "conf"),
        "openvpn": ("server.conf", "conf"),
        "openvpn_success": ("server.conf", "conf"),
        "openvpn_http2": ("server.conf", "conf"),
        "openvpn_obfs4": ("server.conf", "conf"),
        "wireguard_http2": ("wg_http2.conf", "conf"),
        "l2tp_websocket": ("l2tp_ws.conf", "conf"),
        "l2tp": ("l2tp_bundle.conf", "conf"),
        "l2tp_success": ("ipsec.conf", "conf"),
    }

    def __init__(self, output_dir: Optional[str] = None):
        self.output_dir = Path(output_dir or os.getenv("PHOENIX_OUTPUT_DIR", "phoenix-output")) / "configs"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_for_node(self, node: Node, protocols: Optional[List[str]] = None) -> Dict[str, Any]:
        if not node.ip:
            raise ValueError(f"Node {node.node_id} has no IP address")

        selected = protocols or list(self.PROTOCOLS.keys())
        results: Dict[str, Any] = {}

        for proto_name in selected:
            cls = self.PROTOCOLS.get(proto_name)
            if not cls:
                continue
            generator = cls()
            config = generator.generate_config(server_ip=node.ip)
            client_config = generator.generate_client_config(config)
            try:
                server_config = generator.generate_server_config(config)
            except NotImplementedError:
                server_config = json.dumps(config, indent=2)
            results[proto_name] = {
                "config": config,
                "client_config": client_config,
                "server_config": server_config,
            }
            self._write_config(node.node_id, proto_name, config, client_config, server_config)

        return results

    def _write_config(
        self,
        node_id: str,
        protocol: str,
        config: Dict[str, Any],
        client_config: str,
        server_config: str,
    ) -> None:
        dest = self.output_dir / protocol / node_id
        dest.mkdir(parents=True, exist_ok=True)
        (dest / "schema.json").write_text(json.dumps(config, indent=2))

        client_ext = "conf" if protocol in (
            "openvpn",
            "openvpn_success",
            "openvpn_http2",
            "openvpn_cloak",
            "openvpn_obfs4",
            "wireguard",
            "wireguard_amnezia",
            "wireguard_tls",
            "wireguard_http2",
        ) else "txt"
        (dest / f"client.{client_ext}").write_text(client_config)

        server_name, _ = self.SERVER_FILES.get(protocol, ("server.conf", "conf"))
        (dest / server_name).write_text(server_config)

    def generate_all(self, nodes: List[Node]) -> Dict[str, Dict[str, Any]]:
        all_configs: Dict[str, Dict[str, Any]] = {}
        for node in nodes:
            if node.ip:
                all_configs[node.node_id] = self.generate_for_node(node)
        return all_configs
