"""Port rotation for obfuscation."""

from __future__ import annotations

import secrets
from typing import List


class PortRotator:
    def __init__(self, port_pool: List[int] = None):
        self.port_pool = port_pool or [443, 8443, 2053, 2083, 2087, 2096, 8080, 8880]
        self._index = 0

    def current(self) -> int:
        return self.port_pool[self._index]

    def rotate(self) -> int:
        self._index = (self._index + 1) % len(self.port_pool)
        return self.current()

    def random(self) -> int:
        return secrets.choice(self.port_pool)

    def generate_config(self) -> dict:
        return {
            "enabled": True,
            "current_port": self.current(),
            "pool": self.port_pool,
            "rotate_interval": 600,
        }
