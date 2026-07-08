"""Keepalive engine for connection persistence."""

from __future__ import annotations


class KeepaliveEngine:
    def __init__(self, interval: int = 25, timeout: int = 10):
        self.interval = interval
        self.timeout = timeout

    def generate_config(self) -> dict:
        return {
            "enabled": True,
            "interval_seconds": self.interval,
            "timeout_seconds": self.timeout,
            "tcp_keepalive": True,
            "application_ping": True,
        }
