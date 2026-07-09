"""OpenVPN over obfs4 transport."""

from __future__ import annotations

from typing import Any, Dict

from protocols.base import ProtocolBase
from protocols.openvpn_config import OpenVPNConfig


class OpenVPNObfs4Config(ProtocolBase):
    def __init__(self) -> None:
        super().__init__("OpenVPN-obfs4", "2.6")
        self._base = OpenVPNConfig()

    def generate_config(self, server_ip: str, **kwargs: Any) -> Dict[str, Any]:
        cfg = self._base.generate_config(server_ip, **kwargs)
        cfg["protocol"] = "openvpn_obfs4"
        cfg["transport"] = {"type": "obfs4", "proto": "tcp"}
        cfg["obfuscation"] = ["obfs4"]
        return cfg

    def generate_client_config(self, config: Dict[str, Any]) -> str:
        return self._base.generate_client_config(config) + "\n# obfs4 transport wrapper enabled\n"

    def generate_server_config(self, config: Dict[str, Any]) -> str:
        return self._base.generate_server_config(config)
