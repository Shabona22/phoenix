"""OpenVPN success profile (Esfand 1404 field-tested)."""

from __future__ import annotations

import secrets
from typing import Any, Dict

from protocols.base import ProtocolBase


class OpenVPNSuccessConfig(ProtocolBase):
    """OpenVPN over TCP/443 with TLS 1.3 and tls-crypt-v2."""

    def __init__(self) -> None:
        super().__init__("OpenVPN-Success", "2.6")

    def generate_config(self, server_ip: str, **kwargs: Any) -> Dict[str, Any]:
        port = kwargs.get("port", 443)
        username = kwargs.get("username", f"user_{secrets.token_hex(4)}")
        password = kwargs.get("password", self._generate_password(16))
        tls_crypt_key = secrets.token_hex(32)
        return {
            "protocol": "openvpn_success",
            "server": {"ip": server_ip, "port": port, "proto": "tcp"},
            "tls": {
                "version": "1.3",
                "crypt": "tls-crypt-v2",
                "key": tls_crypt_key,
                "cipher": "AES-256-GCM",
                "auth": "SHA256",
            },
            "auth": {"username": username, "password": password},
            "network": {"mtu": 1400, "keepalive": "10 60"},
            "obfuscation": ["tls_1.3", "tcp_443"],
            "dynamic": {"port_rotation": True, "tls_key_rotation": True},
        }

    def generate_client_config(self, config: Dict[str, Any]) -> str:
        tls = config["tls"]
        return f"""client
dev tun
proto tcp
remote {config['server']['ip']} {config['server']['port']}
cipher {tls['cipher']}
auth {tls['auth']}
tls-version-min {tls['version']}
tls-crypt-v2
<tls-crypt-v2>
{tls['key']}
</tls-crypt-v2>
keepalive 10 60
"""

    def generate_server_config(self, config: Dict[str, Any]) -> str:
        tls = config["tls"]
        return f"""port {config['server']['port']}
proto tcp
dev tun
cipher {tls['cipher']}
auth {tls['auth']}
tls-version-min {tls['version']}
# tls-crypt-v2 key provisioned separately
keepalive 10 60
"""
