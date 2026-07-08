import os
import threading
import time
from typing import List, Optional

import requests

from healer.fallback_manager import FallbackManager


class TrafficValidator:
    def __init__(self, fallback_manager: FallbackManager, proxy_url: Optional[str] = None):
        self.fallback = fallback_manager
        self.test_endpoints: List[str] = [
            "https://1.1.1.1/cdn-cgi/trace",
            "https://api.ipify.org?format=json",
        ]
        self.proxy_url = proxy_url or os.getenv("DEFAULT_PROXY", "socks5://127.0.0.1:1080")
        self.failure_count = 0
        self.max_failures = 3
        self.is_running = False
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        self.is_running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self.is_running = False

    def _loop(self) -> None:
        while self.is_running:
            if not self._check():
                self.failure_count += 1
                if self.failure_count >= self.max_failures:
                    self._trigger_fallback()
                    self.failure_count = 0
            else:
                self.failure_count = 0
            time.sleep(30)

    def _check(self) -> bool:
        proxy = {"http": self.proxy_url, "https": self.proxy_url}
        for endpoint in self.test_endpoints:
            try:
                if requests.get(endpoint, proxies=proxy, timeout=5).status_code == 200:
                    return True
            except requests.RequestException:
                continue
        return False

    def _trigger_fallback(self) -> None:
        if not self.fallback.switch_protocol():
            if not self.fallback.switch_node():
                self.fallback.emergency_mode()
