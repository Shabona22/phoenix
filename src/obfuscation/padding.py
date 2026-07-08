"""Traffic padding configuration."""

from __future__ import annotations

import secrets


class Padding:
    def __init__(self, min_bytes: int = 64, max_bytes: int = 512):
        self.min_bytes = min_bytes
        self.max_bytes = max_bytes

    def generate_padding(self) -> bytes:
        size = secrets.randbelow(self.max_bytes - self.min_bytes + 1) + self.min_bytes
        return secrets.token_bytes(size)

    def generate_config(self) -> dict:
        return {
            "enabled": True,
            "min_bytes": self.min_bytes,
            "max_bytes": self.max_bytes,
            "mode": "random",
        }
