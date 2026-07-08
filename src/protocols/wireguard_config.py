from typing import Any, Dict

from utils.crypto import generate_wireguard_keypair

from .base import ProtocolBase


class WireGuardConfig(ProtocolBase):
    def __init__(self):
        super().__init__("WireGuard", "1.0")

    def generate_config(self, server_ip: str, port: int = None, **kwargs) -> Dict[str, Any]:
        if not port:
            port = self._generate_random_port(40000, 60000)
        server_priv, server_pub = generate_wireguard_keypair()
        client_priv, client_pub = generate_wireguard_keypair()
        return {
            "protocol": "wireguard",
            "server": {"ip": server_ip, "port": port},
            "server_keys": {"private": server_priv, "public": server_pub},
            "client_keys": {"private": client_priv, "public": client_pub},
            "address": kwargs.get("address", "10.66.66.2/32"),
            "dns": kwargs.get("dns", "1.1.1.1"),
            "allowed_ips": kwargs.get("allowed_ips", "0.0.0.0/0"),
        }

    def generate_client_config(self, config: Dict[str, Any]) -> str:
        return f"""[Interface]
PrivateKey = {config['client_keys']['private']}
Address = {config['address']}
DNS = {config['dns']}

[Peer]
PublicKey = {config['server_keys']['public']}
Endpoint = {config['server']['ip']}:{config['server']['port']}
AllowedIPs = {config['allowed_ips']}
PersistentKeepalive = 25
"""
