"""Generate decoy traffic noise to blend with real flows."""

from __future__ import annotations

import secrets
from typing import List


class NoiseGenerator:
    def __init__(self, min_size: int = 32, max_size: int = 256):
        self.min_size = min_size
        self.max_size = max_size

    def generate(self, count: int = 1) -> List[bytes]:
        packets: List[bytes] = []
        for _ in range(max(0, count)):
            size = secrets.randbelow(self.max_size - self.min_size + 1) + self.min_size
            packets.append(secrets.token_bytes(size))
        return packets

    def generate_config(self) -> dict:
        return {"enabled": True, "min_size": self.min_size, "max_size": self.max_size}
