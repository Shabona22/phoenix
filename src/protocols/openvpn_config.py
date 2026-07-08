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
            port = kwargs.get("server_port", 1194)
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
                "local_port": 1080,
            },
            "auth": {
                "username": kwargs.get("username", self._generate_password(12)),
                "password": kwargs.get("password", self._generate_password(20)),
            },
            "network": {
                "server_network": "10.8.0.0",
                "netmask": "255.255.255.0",
            },
            "paths": {
                "ca": "/opt/phoenix/openvpn/ca.crt",
                "cert": "/opt/phoenix/openvpn/server.crt",
                "key": "/opt/phoenix/openvpn/server.key",
                "dh": "/opt/phoenix/openvpn/dh.pem",
                "tls_crypt": "/opt/phoenix/openvpn/tls-crypt-v2.key",
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
tls-crypt-v2 {config['paths']['tls_crypt']}
remote-cert-tls server
verb 3
<ca>
# populated by bootstrap from {config['paths']['ca']}
</ca>
"""

    def generate_server_config(self, config: Dict[str, Any]) -> str:
        paths = config["paths"]
        net = config["network"]
        return f"""port {config['server']['port']}
proto tcp
dev tun
ca {paths['ca']}
cert {paths['cert']}
key {paths['key']}
dh {paths['dh']}
tls-crypt-v2 {paths['tls_crypt']}
server {net['server_network']} {net['netmask']}
topology subnet
cipher AES-256-GCM
auth SHA256
tls-version-min 1.3
keepalive 10 120
persist-key
persist-tun
verb 3
explicit-exit-notify 0
"""
