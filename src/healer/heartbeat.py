"""Periodic heartbeat monitoring."""

from __future__ import annotations

import threading
import time
from typing import Callable, List, Optional

import requests


class Heartbeat:
    def __init__(
        self,
        endpoints: Optional[List[str]] = None,
        interval: int = 15,
        proxy_url: Optional[str] = None,
        on_failure: Optional[Callable[[], None]] = None,
    ):
        self.endpoints = endpoints or [
            "https://1.1.1.1/cdn-cgi/trace",
            "https://api.ipify.org?format=json",
        ]
        self.interval = interval
        self.proxy_url = proxy_url
        self.on_failure = on_failure
        self.is_running = False
        self.last_success = False
        self._thread: Optional[threading.Thread] = None

    def _check(self) -> bool:
        proxies = None
        if self.proxy_url:
            proxies = {"http": self.proxy_url, "https": self.proxy_url}
        for endpoint in self.endpoints:
            try:
                resp = requests.get(endpoint, proxies=proxies, timeout=5)
                if resp.status_code == 200:
                    return True
            except requests.RequestException:
                continue
        return False

    def _loop(self) -> None:
        while self.is_running:
            self.last_success = self._check()
            if not self.last_success and self.on_failure:
                self.on_failure()
            time.sleep(self.interval)

    def start(self) -> None:
        if self.is_running:
            return
        self.is_running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self.is_running = False

    def ping(self) -> bool:
        self.last_success = self._check()
        return self.last_success
