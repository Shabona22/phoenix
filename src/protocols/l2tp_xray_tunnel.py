"""L2TP with Xray reverse tunnel for DBF resilience."""

from __future__ import annotations

import random
import secrets
from typing import Any, Dict

from protocols.base import ProtocolBase
class L2TPXrayTunnelConfig(ProtocolBase):
    def __init__(self) -> None:
        super().__init__("L2TP+XrayTunnel", "1.0")

    def generate_config(self, server_ip: str, **kwargs: Any) -> Dict[str, Any]:
        l2tp_port = kwargs.get("l2tp_port", 1701)
        xray_port = kwargs.get("xray_port", random.randint(10000, 65000))
        username = kwargs.get("username", f"user_{secrets.token_hex(4)}")
        password = kwargs.get("password", self._generate_password(16))
        return {
            "protocol": "l2tp_xray",
            "server": {"ip": server_ip, "l2tp_port": l2tp_port, "xray_port": xray_port},
            "tunnel": {
                "type": "xray_reverse",
                "xray_config": {
                    "protocol": "vless",
                    "uuid": secrets.token_hex(16),
                    "streamSettings": {"network": "tcp", "security": "none"},
                },
            },
            "auth": {"username": username, "password": password},
            "dynamic": {"port_rotation": True, "tunnel_rotation": True},
            "tls": False,
        }

    def generate_client_config(self, config: Dict[str, Any]) -> str:
        server = config["server"]
        tunnel = config["tunnel"]
        auth = config["auth"]
        return f"""L2TP/IPSec (via Xray Reverse Tunnel)
Server: {server['ip']}
L2TP Port: {server['l2tp_port']}
Xray Port: {server['xray_port']}
Username: {auth['username']}
Password: {auth['password']}
Tunnel Type: {tunnel['type']}
"""

    def generate_server_config(self, config: Dict[str, Any]) -> str:
        server = config["server"]
        return f"""# L2TP + Xray reverse tunnel server
L2TP_PORT={server['l2tp_port']}
XRAY_PORT={server['xray_port']}
XRAY_SECURITY=none
"""
