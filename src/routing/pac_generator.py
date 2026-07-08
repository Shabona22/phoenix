"""PAC file generator for split tunneling."""

from __future__ import annotations

from typing import List


class PACGenerator:
    def __init__(self, proxy_host: str = "127.0.0.1", proxy_port: int = 1080):
        self.proxy_host = proxy_host
        self.proxy_port = proxy_port

    def generate(self, direct_domains: List[str] = None, proxy_domains: List[str] = None) -> str:
        direct = direct_domains or ["localhost", "127.0.0.1", "*.local"]
        proxy = proxy_domains or ["*.ir", "*.gov.ir"]

        direct_checks = " || ".join(f'dnsDomainIs(host, "{d}")' for d in direct)
        proxy_checks = " || ".join(f'shExpMatch(host, "{d}")' for d in proxy)

        return f"""function FindProxyForURL(url, host) {{
    if (isPlainHostName(host) || {direct_checks or "false"}) {{
        return "DIRECT";
    }}
    if ({proxy_checks or "false"}) {{
        return "SOCKS5 {self.proxy_host}:{self.proxy_port}";
    }}
    return "SOCKS5 {self.proxy_host}:{self.proxy_port}";
}}
"""
