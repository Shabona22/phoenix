"""WebRTC leak check – STUN-based detection scaffold."""

from __future__ import annotations

from typing import Dict, List


class WebRTCLeakCheck:
    """Headless environments cannot run real WebRTC; this module documents and simulates checks."""

    STUN_SERVERS = [
        "stun:stun.l.google.com:19302",
        "stun:stun1.l.google.com:19302",
    ]

    def __init__(self):
        self._local_candidates: List[str] = []

    def check(self, local_candidates: List[str] = None) -> Dict[str, object]:
        candidates = local_candidates or self._local_candidates
        private_ranges = ("10.", "172.16.", "192.168.")
        leaked = any(c.startswith(private_ranges) for c in candidates)
        return {
            "leaked": leaked,
            "candidates": candidates,
            "stun_servers": self.STUN_SERVERS,
            "note": "Real WebRTC check requires browser context; use manual verification in browser.",
        }

    def is_clean(self, local_candidates: List[str] = None) -> bool:
        return not self.check(local_candidates)["leaked"]
