"""IP leak detection – compare direct vs proxy IP."""

from __future__ import annotations

import os
from typing import Dict, Optional

import requests


class IPLeakCheck:
    ENDPOINTS = [
        "https://api.ipify.org?format=json",
        "https://ifconfig.me/ip",
    ]

    def __init__(self, proxy_url: Optional[str] = None):
        self.proxy_url = proxy_url or os.getenv("DEFAULT_PROXY", "socks5://127.0.0.1:1080")

    def _fetch_ip(self, use_proxy: bool = False) -> Optional[str]:
        proxies = None
        if use_proxy:
            proxies = {"http": self.proxy_url, "https": self.proxy_url}

        for endpoint in self.ENDPOINTS:
            try:
                resp = requests.get(endpoint, proxies=proxies, timeout=5)
                if resp.status_code == 200:
                    text = resp.text.strip()
                    if text.startswith("{"):
                        return resp.json().get("ip", text)
                    return text
            except requests.RequestException:
                continue
        return None

    def check(self) -> Dict[str, object]:
        direct_ip = self._fetch_ip(use_proxy=False)
        proxy_ip = self._fetch_ip(use_proxy=True)
        leaked = bool(direct_ip and proxy_ip and direct_ip == proxy_ip)
        return {
            "direct_ip": direct_ip,
            "proxy_ip": proxy_ip,
            "leaked": leaked,
            "message": "IP leak detected" if leaked else "No IP leak detected",
        }

    def is_clean(self) -> bool:
        return not self.check()["leaked"]
