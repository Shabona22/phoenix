"""Decoy DNS answers for fake-IP / routing camouflage."""

from __future__ import annotations

from typing import Dict, List


class FakeIPResolver:
    DECOY_IPS = ["198.18.0.1", "198.18.0.2", "198.18.0.3"]

    def __init__(self, decoy_ips: List[str] | None = None):
        self.decoy_ips = decoy_ips or self.DECOY_IPS

    def resolve(self, hostname: str) -> str:
        if not hostname:
            return self.decoy_ips[0]
        idx = sum(ord(c) for c in hostname) % len(self.decoy_ips)
        return self.decoy_ips[idx]

    def generate_config(self) -> Dict[str, object]:
        return {
            "enabled": True,
            "decoy_ips": list(self.decoy_ips),
            "note": "Use with routing rules; does not perform live DNS queries.",
        }
