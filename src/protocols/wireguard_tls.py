"""WireGuard over TLS tunnel profile."""

from __future__ import annotations

import random
import secrets
from typing import Any, Dict

from protocols.base import ProtocolBase


class WireGuardTLSConfig(ProtocolBase):
    """Encapsulate WireGuard signaling inside TLS-like transport."""

    def __init__(self) -> None:
        super().__init__("WireGuard-TLS", "1.0")

    def generate_config(self, server_ip: str, **kwargs: Any) -> Dict[str, Any]:
        port = kwargs.get("port", 443)
        wg_port = kwargs.get("wg_port", random.randint(10000, 65000))
        return {
            "protocol": "wireguard_tls",
            "server": {"ip": server_ip, "port": port},
            "wireguard": {
                "private_key": secrets.token_hex(32),
                "public_key": secrets.token_hex(32),
                "preshared_key": secrets.token_hex(32),
                "inner_port": wg_port,
            },
            "tls": {"version": "1.3", "sni": kwargs.get("sni", "cdn-node.example.com")},
            "dynamic": {"port_rotation": True, "sni_rotation": True},
        }

    def generate_client_config(self, config: Dict[str, Any]) -> str:
        wg = config["wireguard"]
        return f"""[Interface]
PrivateKey = {wg['private_key']}
Address = 10.10.0.2/32
[Peer]
PublicKey = {wg['public_key']}
PresharedKey = {wg['preshared_key']}
Endpoint = {config['server']['ip']}:{config['server']['port']}
AllowedIPs = 0.0.0.0/0
PersistentKeepalive = 25
# Encapsulation: wg-tls
"""

    def generate_server_config(self, config: Dict[str, Any]) -> str:
        return f"""# wireguard over tls
LISTEN_TLS_PORT={config['server']['port']}
INNER_WG_PORT={config['wireguard']['inner_port']}
TLS_VERSION={config['tls']['version']}
"""
