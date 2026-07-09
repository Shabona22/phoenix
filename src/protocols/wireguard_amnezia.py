"""WireGuard with AmneziaWG obfuscation for DBF environments."""

from __future__ import annotations

import random
import secrets
from typing import Any, Dict

from protocols.base import ProtocolBase
class WireGuardAmneziaConfig(ProtocolBase):
    def __init__(self) -> None:
        super().__init__("WireGuard+AmneziaWG", "1.0")

    def generate_config(self, server_ip: str, **kwargs: Any) -> Dict[str, Any]:
        private_key = secrets.token_hex(32)
        public_key = secrets.token_hex(32)
        preshared_key = secrets.token_hex(32)
        port = kwargs.get("port", random.randint(10000, 65000))
        return {
            "protocol": "wireguard_amnezia",
            "server": {"ip": server_ip, "port": port},
            "keys": {
                "private": private_key,
                "public": public_key,
                "preshared": preshared_key,
            },
            "obfuscation": {
                "enabled": True,
                "type": "amneziawg",
                "mtu": random.randint(1280, 1500),
                "padding": random.randint(0, 100),
                "jitter": random.randint(10, 100),
            },
            "network": {"dns": "1.1.1.1", "allowed_ips": "0.0.0.0/0"},
            "dynamic": {"port_rotation": True, "mtu_rotation": True},
        }

    def generate_client_config(self, config: Dict[str, Any]) -> str:
        keys = config["keys"]
        obfs = config["obfuscation"]
        return f"""[Interface]
PrivateKey = {keys['private']}
Address = 10.0.0.2/32
DNS = {config['network']['dns']}
[Peer]
PublicKey = {keys['public']}
PresharedKey = {keys['preshared']}
AllowedIPs = {config['network']['allowed_ips']}
Endpoint = {config['server']['ip']}:{config['server']['port']}
PersistentKeepalive = 25
Obfuscation = {obfs['type']}
MTU = {obfs['mtu']}
Jitter = {obfs['jitter']}
"""

    def generate_server_config(self, config: Dict[str, Any]) -> str:
        keys = config["keys"]
        return f"""[Interface]
PrivateKey = {keys['private']}
Address = 10.0.0.1/24
ListenPort = {config['server']['port']}
MTU = {config['obfuscation']['mtu']}
[Peer]
PublicKey = {keys['public']}
PresharedKey = {keys['preshared']}
AllowedIPs = 10.0.0.2/32
"""
