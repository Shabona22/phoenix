"""Generate configs with dynamic port/SNI rotation based on threat level."""

from __future__ import annotations

from typing import Any, Dict, Optional

from obfuscation.port_rotator import PortRotator
from obfuscation.sni_rotator import SNIRotator


class DynamicConfigGenerator:
    def __init__(self, sni_hosts: Optional[list[str]] = None, ports: Optional[list[int]] = None):
        self.sni = SNIRotator(sni_hosts or ["www.cloudflare.com", "www.microsoft.com"])
        self.ports = PortRotator(ports or [443, 8443, 2053])

    def adapt(self, base_config: Dict[str, Any], threat_level: str = "medium") -> Dict[str, Any]:
        cfg = dict(base_config)
        server = dict(cfg.get("server", {}))
        if threat_level in ("medium", "high"):
            server["port"] = self.ports.rotate()
            cfg["sni"] = self.sni.rotate()
        if threat_level == "high":
            cfg["obfuscation"] = {"enabled": True, "mode": "fragment+noise"}
        cfg["server"] = server
        cfg["dynamic"] = True
        return cfg
