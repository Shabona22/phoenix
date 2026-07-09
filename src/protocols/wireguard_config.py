from typing import Any, Dict

from utils.crypto import generate_wireguard_keypair

from .base import ProtocolBase


class WireGuardConfig(ProtocolBase):
    def __init__(self):
        super().__init__("WireGuard", "1.0")

    def generate_config(self, server_ip: str, port: int = None, **kwargs) -> Dict[str, Any]:
        if not port:
            port = kwargs.get("server_port", 51820)
        server_priv, server_pub = generate_wireguard_keypair()
        client_priv, client_pub = generate_wireguard_keypair()
        return {
            "protocol": "wireguard",
            "server": {"ip": server_ip, "port": port},
            "server_keys": {"private": server_priv, "public": server_pub},
            "client_keys": {"private": client_priv, "public": client_pub},
            "server_address": kwargs.get("server_address", "10.66.66.1/24"),
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

    def generate_server_config(self, config: Dict[str, Any]) -> str:
        client_ip = config["address"].split("/")[0]
        return f"""[Interface]
PrivateKey = {config['server_keys']['private']}
Address = {config['server_address']}
ListenPort = {config['server']['port']}
PostUp = iptables -A FORWARD -i wg0 -j ACCEPT; iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
PostDown = iptables -D FORWARD -i wg0 -j ACCEPT; iptables -t nat -D POSTROUTING -o eth0 -j MASQUERADE

[Peer]
PublicKey = {config['client_keys']['public']}
AllowedIPs = {client_ip}/32
"""
