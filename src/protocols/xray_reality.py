"""Xray Reality-focused config generator."""

from __future__ import annotations

from typing import Any, Dict

from protocols.base import ProtocolBase
from protocols.xray_config import XrayConfig


class XrayRealityConfig(ProtocolBase):
    def __init__(self) -> None:
        super().__init__("XrayReality", "1.8")
        self._base = XrayConfig()

    def generate_config(self, server_ip: str, **kwargs: Any) -> Dict[str, Any]:
        cfg = self._base.generate_config(server_ip, **kwargs)
        cfg["protocol"] = "xray_reality"
        cfg["transport"]["security"] = "reality"
        cfg["tls"] = True
        return cfg

    def generate_client_config(self, config: Dict[str, Any]) -> str:
        return self._base.generate_client_config(config)

    def generate_server_config(self, config: Dict[str, Any]) -> str:
        return self._base.generate_server_config(config)
