"""L2TP over Xray VLESS+WebSocket tunnel."""

from __future__ import annotations

import random
import secrets
from typing import Any, Dict

from protocols.base import ProtocolBase


class L2TPWebSocketConfig(ProtocolBase):
    def __init__(self) -> None:
        super().__init__("L2TP-WebSocket", "1.0")

    def generate_config(self, server_ip: str, **kwargs: Any) -> Dict[str, Any]:
        l2tp_port = kwargs.get("l2tp_port", 1701)
        ws_port = kwargs.get("ws_port", random.randint(10000, 65000))
        path = kwargs.get("path", "/ws/" + secrets.token_hex(4))
        username = kwargs.get("username", f"user_{secrets.token_hex(4)}")
        password = kwargs.get("password", self._generate_password(16))
        return {
            "protocol": "l2tp_websocket",
            "server": {"ip": server_ip, "l2tp_port": l2tp_port, "ws_port": ws_port},
            "tunnel": {
                "type": "xray_websocket",
                "xray_config": {
                    "protocol": "vless",
                    "uuid": secrets.token_hex(16),
                    "streamSettings": {
                        "network": "ws",
                        "security": "tls",
                        "wsSettings": {"path": path},
                    },
                },
            },
            "auth": {"username": username, "password": password},
            "dynamic": {"path_rotation": True, "port_rotation": True},
            "tls": True,
        }

    def generate_client_config(self, config: Dict[str, Any]) -> str:
        server = config["server"]
        tunnel = config["tunnel"]
        auth = config["auth"]
        path = tunnel["xray_config"]["streamSettings"]["wsSettings"]["path"]
        return f"""L2TP/IPsec via Xray WebSocket
Server: {server['ip']}
L2TP Port: {server['l2tp_port']}
Xray WS Port: {server['ws_port']}
WS Path: {path}
Username: {auth['username']}
Password: {auth['password']}
Tunnel Type: {tunnel['type']}
"""

    def generate_server_config(self, config: Dict[str, Any]) -> str:
        server = config["server"]
        return f"""# L2TP + Xray WebSocket
L2TP_PORT={server['l2tp_port']}
WS_PORT={server['ws_port']}
"""
