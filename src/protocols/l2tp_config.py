import secrets
from typing import Any, Dict

from .base import ProtocolBase


class L2TPConfig(ProtocolBase):
    def __init__(self):
        super().__init__("L2TP/IPSec", "1.0")

    def generate_config(self, server_ip: str, psk: str = None, **kwargs) -> Dict[str, Any]:
        if not psk:
            psk = secrets.token_hex(20)
        return {
            "protocol": "l2tp_ipsec",
            "server": {"ip": server_ip, "ipsec_port": 4500, "l2tp_port": 1701},
            "ipsec": {
                "phase1": {"algorithm": "aes256-sha256-modp2048", "lifetime": "28800s"},
                "phase2": {"algorithm": "aes256-sha256", "lifetime": "3600s"},
                "pre_shared_key": psk,
                "nat_traversal": True,
            },
            "auth": {
                "username": kwargs.get("username", f"user_{secrets.token_hex(4)}"),
                "password": kwargs.get("password", self._generate_password(16)),
            },
        }

    def generate_client_config(self, config: Dict[str, Any]) -> str:
        return f"""L2TP/IPSec PSK
Server: {config['server']['ip']}
PSK: {config['ipsec']['pre_shared_key']}
Username: {config['auth']['username']}
Password: {config['auth']['password']}
NAT Traversal: Enabled
"""
