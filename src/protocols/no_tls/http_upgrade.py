"""HTTP Upgrade tunnel without TLS."""

from __future__ import annotations

import secrets
from typing import Any, Dict

from protocols.base import ProtocolBase


class HTTPUpgradeConfig(ProtocolBase):
    def __init__(self) -> None:
        super().__init__("HTTPUpgrade", "1.0")

    def generate_config(self, server_ip: str, **kwargs: Any) -> Dict[str, Any]:
        port = kwargs.get("port", 80)
        path = kwargs.get("path", "/upgrade/" + secrets.token_hex(4))
        return {
            "protocol": "http_upgrade",
            "server": {"ip": server_ip, "port": port},
            "network": {
                "type": "http",
                "upgrade": "websocket",
                "path": path,
                "headers": {"Connection": "Upgrade", "Upgrade": "websocket"},
            },
            "dynamic": {"path_rotation": True},
            "obfuscation": [],
            "tls": False,
        }

    def generate_client_config(self, config: Dict[str, Any]) -> str:
        server = config["server"]
        path = config["network"]["path"]
        return f"http://{server['ip']}:{server['port']}{path}"
