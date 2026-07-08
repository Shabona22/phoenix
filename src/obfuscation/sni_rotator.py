"""SNI rotation for obfuscation."""

from __future__ import annotations

import random
from typing import List


class SNIRotator:
    DEFAULT_SNIS = [
        "www.microsoft.com",
        "www.cloudflare.com",
        "www.bing.com",
        "www.apple.com",
        "www.amazon.com",
    ]

    def __init__(self, sni_list: List[str] = None):
        self.sni_list = sni_list or self.DEFAULT_SNIS
        self._index = 0

    def current(self) -> str:
        return self.sni_list[self._index]

    def rotate(self) -> str:
        self._index = (self._index + 1) % len(self.sni_list)
        return self.current()

    def random(self) -> str:
        return random.choice(self.sni_list)

    def generate_config(self) -> dict:
        return {"sni": self.current(), "rotate_interval": 300, "pool": self.sni_list}
