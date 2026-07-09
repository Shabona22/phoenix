"""Plain TCP (no TLS) protocol config."""

from __future__ import annotations

import secrets
from typing import Any, Dict

from protocols.base import ProtocolBase


class TCPPlainConfig(ProtocolBase):
    def __init__(self) -> None:
        super().__init__("TCPPlain", "1.0")

    def generate_config(self, server_ip: str, **kwargs: Any) -> Dict[str, Any]:
        port = kwargs.get("port", self._generate_random_port(10000, 65000))
        return {
            "protocol": "tcp_plain",
            "server": {"ip": server_ip, "port": port},
            "network": {"type": "tcp", "keepalive": secrets.randbelow(51) + 10},
            "dynamic": {"port_rotation": True},
            "obfuscation": [],
            "tls": False,
        }

    def generate_client_config(self, config: Dict[str, Any]) -> str:
        server = config["server"]
        return f"tcp://{server['ip']}:{server['port']}"
