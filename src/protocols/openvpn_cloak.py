"""OpenVPN with Cloak obfuscation for DBF environments."""

from __future__ import annotations

import secrets
import random
import string
from typing import Any, Dict

from protocols.base import ProtocolBase
class OpenVPNCloakConfig(ProtocolBase):
    def __init__(self) -> None:
        super().__init__("OpenVPN+Cloak", "2.6")

    def _generate_random_domain(self) -> str:
        prefixes = ["cdn", "api", "static", "media", "img"]
        names = ["cloud", "server", "node", "edge", "nexus"]
        tlds = [".com", ".org", ".net", ".xyz", ".online"]
        random_part = "".join(random.choices(string.ascii_lowercase, k=6))
        return random.choice(prefixes) + random.choice(names) + random_part + random.choice(tlds)

    def generate_config(self, server_ip: str, **kwargs: Any) -> Dict[str, Any]:
        port = kwargs.get("port", 443)
        username = kwargs.get("username", self._generate_password(12))
        password = kwargs.get("password", self._generate_password(20))
        cloak_key = secrets.token_hex(32)
        cloak_pub = secrets.token_hex(32)
        cloak_target = self._generate_random_domain()
        return {
            "protocol": "openvpn_cloak",
            "server": {"ip": server_ip, "port": port},
            "cloak": {
                "enabled": True,
                "key": cloak_key,
                "pub": cloak_pub,
                "target": cloak_target,
                "proxy": f"https://{cloak_target}",
                "encryption": "aes-256-gcm",
            },
            "auth": {"username": username, "password": password},
            "network": {"mtu": 1400, "keepalive": "10 60"},
            "obfuscation": ["cloak"],
            "dynamic": {"port_rotation": True, "domain_rotation": True},
        }

    def generate_client_config(self, config: Dict[str, Any]) -> str:
        cloak = config["cloak"]
        return f"""client
dev tun
proto tcp
remote {config['server']['ip']} {config['server']['port']}
<http-proxy>
  {config['server']['ip']} {config['server']['port']}
  https
</http-proxy>
cloak-key {cloak['key']}
cloak-pub {cloak['pub']}
cloak-target {cloak['target']}
cipher AES-256-GCM
auth SHA256
keepalive 10 60
"""

    def generate_server_config(self, config: Dict[str, Any]) -> str:
        return (
            "port {port}\nproto tcp\ndev tun\ncipher AES-256-GCM\nauth SHA256\n"
            "keepalive 10 60\n".format(port=config["server"]["port"])
        )
