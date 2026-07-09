"""OpenVPN over TCP/443 with HTTP/2 ALPN camouflage."""

from __future__ import annotations

import secrets
from typing import Any, Dict

from protocols.base import ProtocolBase


class OpenVPNHttp2Config(ProtocolBase):
    def __init__(self) -> None:
        super().__init__("OpenVPN-HTTP2", "2.6")

    def generate_config(self, server_ip: str, **kwargs: Any) -> Dict[str, Any]:
        port = kwargs.get("port", 443)
        tls_crypt_key = secrets.token_hex(32)
        return {
            "protocol": "openvpn_http2",
            "server": {"ip": server_ip, "port": port, "proto": "tcp"},
            "tls": {
                "version": "1.3",
                "crypt": "tls-crypt-v2",
                "key": tls_crypt_key,
                "cipher": "AES-256-GCM",
                "auth": "SHA256",
                "alpn": "h2",
            },
            "obfuscation": ["http2_alpn", "tcp_443"],
            "dynamic": {"port_rotation": True, "alpn_rotation": False},
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
http-proxy-option CUSTOM-HEADER ALPN {tls['alpn']}
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
# ALPN h2 for HTTP/2 camouflage
keepalive 10 60
"""
