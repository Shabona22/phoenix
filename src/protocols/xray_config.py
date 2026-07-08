import secrets
from typing import Any, Dict

from utils.crypto import generate_uuid

from .base import ProtocolBase


class XrayConfig(ProtocolBase):
    def __init__(self):
        super().__init__("Xray", "1.8")

    def generate_config(self, server_ip: str, port: int = None, **kwargs) -> Dict[str, Any]:
        if not port:
            port = self._generate_random_port(10000, 65000)
        uuid = kwargs.get("uuid", generate_uuid())
        return {
            "protocol": "xray",
            "server": {"ip": server_ip, "port": port, "proto": "tcp"},
            "uuid": uuid,
            "transport": {
                "type": "tcp",
                "security": "reality",
                "reality": {
                    "dest": kwargs.get("dest", "www.microsoft.com:443"),
                    "server_names": [kwargs.get("sni", "www.microsoft.com")],
                    "private_key": secrets.token_hex(32),
                    "short_ids": [secrets.token_hex(4)],
                },
            },
            "fallback": {
                "enabled": True,
                "type": "tcp",
                "dest": "127.0.0.1:8080",
            },
        }

    def generate_client_config(self, config: Dict[str, Any]) -> str:
        return f"""vless://{config['uuid']}@{config['server']['ip']}:{config['server']['port']}
security=reality
type=tcp
sni={config['transport']['reality']['server_names'][0]}
"""
