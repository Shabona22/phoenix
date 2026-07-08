from typing import Any, Dict

from .base import ProtocolBase


class ShadowsocksConfig(ProtocolBase):
    def __init__(self):
        super().__init__("Shadowsocks", "2022")
        self.ciphers = ["aes-256-gcm", "chacha20-ietf-poly1305"]

    def generate_config(self, server_ip: str, port: int = None, **kwargs) -> Dict[str, Any]:
        if not port:
            port = self._generate_random_port(10000, 65000)
        cipher = kwargs.get("cipher", "aes-256-gcm")
        return {
            "protocol": "shadowsocks",
            "server": {"ip": server_ip, "port": port},
            "cipher": cipher,
            "password": kwargs.get("password", self._generate_password(24)),
            "plugin": kwargs.get("plugin", ""),
            "plugin_opts": kwargs.get("plugin_opts", ""),
        }

    def generate_client_config(self, config: Dict[str, Any]) -> str:
        return f"""{config['cipher']}:{config['password']}@{config['server']['ip']}:{config['server']['port']}
"""
