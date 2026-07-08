"""Traffic jitter configuration."""

from __future__ import annotations

import random


class Jitter:
    def __init__(self, min_ms: int = 10, max_ms: int = 200):
        self.min_ms = min_ms
        self.max_ms = max_ms

    def next_delay_ms(self) -> int:
        return random.randint(self.min_ms, self.max_ms)

    def generate_config(self) -> dict:
        return {
            "enabled": True,
            "min_ms": self.min_ms,
            "max_ms": self.max_ms,
            "distribution": "uniform",
        }
