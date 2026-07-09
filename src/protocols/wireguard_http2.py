"""WireGuard encapsulated behind HTTP/2 TLS transport."""

from __future__ import annotations

import random
import secrets
from typing import Any, Dict

from protocols.base import ProtocolBase


class WireGuardHttp2Config(ProtocolBase):
    def __init__(self) -> None:
        super().__init__("WireGuard-HTTP2", "1.0")

    def generate_config(self, server_ip: str, **kwargs: Any) -> Dict[str, Any]:
        tls_port = kwargs.get("port", 443)
        inner_port = kwargs.get("inner_port", random.randint(10000, 65000))
        return {
            "protocol": "wireguard_http2",
            "server": {"ip": server_ip, "port": tls_port},
            "wireguard": {
                "private_key": secrets.token_hex(32),
                "public_key": secrets.token_hex(32),
                "preshared_key": secrets.token_hex(32),
                "inner_port": inner_port,
            },
            "transport": {"type": "http2", "alpn": "h2", "tls_version": "1.3"},
            "dynamic": {"port_rotation": True, "sni_rotation": True},
        }

    def generate_client_config(self, config: Dict[str, Any]) -> str:
        wg = config["wireguard"]
        return f"""[Interface]
PrivateKey = {wg['private_key']}
Address = 10.12.0.2/32
[Peer]
PublicKey = {wg['public_key']}
PresharedKey = {wg['preshared_key']}
Endpoint = {config['server']['ip']}:{config['server']['port']}
AllowedIPs = 0.0.0.0/0
PersistentKeepalive = 25
# Encapsulation: wireguard-http2 (inner UDP {wg['inner_port']})
"""

    def generate_server_config(self, config: Dict[str, Any]) -> str:
        wg = config["wireguard"]
        return f"""# wireguard over http2
TLS_PORT={config['server']['port']}
INNER_WG_PORT={wg['inner_port']}
ALPN=h2
"""
