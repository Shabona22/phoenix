import json
import secrets
from typing import Any, Dict

from utils.crypto import generate_uuid, generate_x25519_reality_keypair

from .base import ProtocolBase


class XrayConfig(ProtocolBase):
    def __init__(self):
        super().__init__("Xray", "1.8")

    def generate_config(self, server_ip: str, port: int = None, **kwargs) -> Dict[str, Any]:
        if not port:
            port = self._generate_random_port(10000, 65000)
        uuid = kwargs.get("uuid", generate_uuid())
        private_key, public_key = generate_x25519_reality_keypair()
        short_id = secrets.token_hex(4)
        sni = kwargs.get("sni", "www.microsoft.com")
        return {
            "protocol": "xray",
            "server": {"ip": server_ip, "port": port, "proto": "tcp"},
            "uuid": uuid,
            "transport": {
                "type": "tcp",
                "security": "reality",
                "reality": {
                    "dest": kwargs.get("dest", f"{sni}:443"),
                    "server_names": [sni],
                    "private_key": private_key,
                    "public_key": public_key,
                    "short_ids": [short_id],
                },
            },
            "fallback": {
                "enabled": True,
                "type": "tcp",
                "dest": "127.0.0.1:8080",
            },
        }

    def generate_client_config(self, config: Dict[str, Any]) -> str:
        reality = config["transport"]["reality"]
        return f"""vless://{config['uuid']}@{config['server']['ip']}:{config['server']['port']}
security=reality
type=tcp
sni={reality['server_names'][0]}
pbk={reality['public_key']}
sid={reality['short_ids'][0]}
flow=xtls-rprx-vision
"""

    def generate_server_config(self, config: Dict[str, Any]) -> str:
        reality = config["transport"]["reality"]
        server_cfg = {
            "log": {"loglevel": "warning"},
            "inbounds": [
                {
                    "port": config["server"]["port"],
                    "protocol": "vless",
                    "settings": {
                        "clients": [
                            {
                                "id": config["uuid"],
                                "flow": "xtls-rprx-vision",
                            }
                        ],
                        "decryption": "none",
                    },
                    "streamSettings": {
                        "network": "tcp",
                        "security": "reality",
                        "realitySettings": {
                            "dest": reality["dest"],
                            "serverNames": reality["server_names"],
                            "privateKey": reality["private_key"],
                            "shortIds": reality["short_ids"],
                        },
                    },
                }
            ],
            "outbounds": [{"protocol": "freedom", "tag": "direct"}],
        }
        return json.dumps(server_cfg, indent=2)
