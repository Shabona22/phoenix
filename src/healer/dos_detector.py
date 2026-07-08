"""DoS / rate-limit anomaly detection."""

from __future__ import annotations

import time
from collections import deque
from typing import Deque, Dict


class DoSDetector:
    def __init__(self, window_seconds: int = 60, max_requests: int = 100):
        self.window_seconds = window_seconds
        self.max_requests = max_requests
        self._events: Deque[float] = deque()

    def record_request(self) -> None:
        now = time.time()
        self._events.append(now)
        self._prune(now)

    def _prune(self, now: float) -> None:
        cutoff = now - self.window_seconds
        while self._events and self._events[0] < cutoff:
            self._events.popleft()

    def is_under_attack(self) -> bool:
        self._prune(time.time())
        return len(self._events) > self.max_requests

    def status(self) -> Dict[str, object]:
        self._prune(time.time())
        count = len(self._events)
        return {
            "request_count": count,
            "max_requests": self.max_requests,
            "window_seconds": self.window_seconds,
            "under_attack": count > self.max_requests,
        }
