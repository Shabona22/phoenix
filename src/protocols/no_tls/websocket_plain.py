"""WebSocket plain (no TLS) – highest DBF stability priority."""

from __future__ import annotations

import secrets
from typing import Any, Dict

from protocols.base import ProtocolBase


class WebSocketPlainConfig(ProtocolBase):
    def __init__(self) -> None:
        super().__init__("WebSocketPlain", "1.0")

    def generate_config(self, server_ip: str, **kwargs: Any) -> Dict[str, Any]:
        port = kwargs.get("port", self._generate_random_port(10000, 65000))
        path = kwargs.get("path", "/" + secrets.token_hex(8))
        return {
            "protocol": "websocket_plain",
            "server": {"ip": server_ip, "port": port},
            "network": {
                "type": "ws",
                "path": path,
                "headers": {
                    "Host": f"cdn-{secrets.token_hex(4)}.com",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0",
                },
            },
            "dynamic": {"port_rotation": True, "path_rotation": True},
            "obfuscation": [],
            "tls": False,
        }

    def generate_client_config(self, config: Dict[str, Any]) -> str:
        server = config["server"]
        network = config["network"]
        return (
            f"ws://{server['ip']}:{server['port']}{network['path']}\n"
            f"Host: {network['headers']['Host']}\n"
        )
