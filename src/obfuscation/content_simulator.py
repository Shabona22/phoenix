"""Shape traffic to resemble popular services, defeating DPI/ML classifiers.

The simulator produces synthetic decoy payloads and timing hints. It never sends
data itself; it only describes what a realistic flow should look like so the
transport layer can pad/segment/schedule accordingly.
"""

from __future__ import annotations

import random
import time
from typing import Callable, Dict, List


class ContentSimulator:
    """Generate decoy payloads matching well-known service traffic profiles."""

    def __init__(self, seed: int | None = None):
        self._rng = random.Random(seed)
        self.patterns: Dict[str, Callable[[], bytes]] = {
            "youtube": self._youtube_pattern,
            "whatsapp": self._whatsapp_pattern,
            "instagram": self._instagram_pattern,
            "google_docs": self._google_docs_pattern,
            "netflix": self._netflix_pattern,
        }
        self.current_pattern = "youtube"

    def _rand_bytes(self, n: int) -> bytes:
        return self._rng.getrandbits(8 * n).to_bytes(n, "big") if n else b""

    def _youtube_pattern(self) -> bytes:
        expire = self._rng.randint(1700000000, 1800000000)
        return b"GET /videoplayback?expire=" + str(expire).encode() + b"&key=yt" + self._rand_bytes(100)

    def _whatsapp_pattern(self) -> bytes:
        return b"POST /v1/messages " + self._rand_bytes(50)

    def _instagram_pattern(self) -> bytes:
        return b"GET /api/v1/feed/ " + self._rand_bytes(80)

    def _google_docs_pattern(self) -> bytes:
        return b"POST /docs/api/v1/update " + self._rand_bytes(200)

    def _netflix_pattern(self) -> bytes:
        return b"GET /watch/" + self._rand_bytes(30) + b"?quality=4K" + self._rand_bytes(150)

    def get_random_traffic(self) -> bytes:
        self.current_pattern = self._rng.choice(list(self.patterns))
        return self.patterns[self.current_pattern]()

    def change_pattern(self, pattern_name: str) -> bool:
        if pattern_name in self.patterns:
            self.current_pattern = pattern_name
            return True
        return False

    def generate_flow(self, count: int) -> List[bytes]:
        """Deterministic decoy flow of `count` packets (no sleeping)."""
        return [self.get_random_traffic() for _ in range(max(0, count))]

    def generate_traffic_flow(self, duration_seconds: float) -> List[bytes]:
        """Time-bounded decoy flow with randomized inter-packet gaps."""
        traffic: List[bytes] = []
        start = time.monotonic()
        while time.monotonic() - start < duration_seconds:
            traffic.append(self.get_random_traffic())
            time.sleep(self._rng.uniform(0.1, 0.3))
        return traffic

    def generate_config(self) -> Dict[str, object]:
        return {
            "enabled": True,
            "current_pattern": self.current_pattern,
            "patterns": list(self.patterns),
            "packet_size_range": [50, 1500],
            "interval_range_seconds": [0.1, 3.0],
        }
