import secrets
from typing import Any, Dict

from .base import ProtocolBase


class OpenVPNConfig(ProtocolBase):
    def __init__(self):
        super().__init__("OpenVPN", "2.6")
        self.obfs_methods = ["obfs4", "obfs3"]
        self.ciphers = ["AES-256-GCM", "CHACHA20-POLY1305"]

    def generate_config(self, server_ip: str, port: int = None, **kwargs) -> Dict[str, Any]:
        if not port:
            port = self._generate_random_port(8000, 65000)
        return {
            "protocol": "openvpn",
            "server": {"ip": server_ip, "port": port, "proto": "tcp"},
            "cryptography": {
                "cipher": "AES-256-GCM",
                "auth": "SHA256",
                "tls_version": "1.3",
                "tls_crypt_v2": True,
            },
            "obfuscation": {
                "enabled": True,
                "method": "obfs4",
                "param": secrets.token_hex(16),
            },
            "auth": {
                "username": kwargs.get("username", self._generate_password(12)),
                "password": kwargs.get("password", self._generate_password(20)),
            },
        }

    def generate_client_config(self, config: Dict[str, Any]) -> str:
        return f"""client
dev tun
proto tcp
remote {config['server']['ip']} {config['server']['port']}
cipher AES-256-GCM
auth SHA256
tls-version-min 1.3
tls-crypt-v2
obfsproxy obfs4 127.0.0.1:1080
<ca>
{config.get('ca_cert', '')}
</ca>
"""
