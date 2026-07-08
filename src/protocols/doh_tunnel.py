"""DNS-over-HTTPS tunnel for when all VPN protocols are blocked."""

from __future__ import annotations

import base64
import hashlib
import os
import time
from typing import Any, Dict, List, Optional
from urllib.parse import quote


class DoHTunnel:
    """Encode payloads as DNS query labels and send via DoH GET requests."""

    CHUNK_SIZE = 50
    DEFAULT_SERVER = "https://1.1.1.1/dns-query"

    def __init__(self, dns_server: str = DEFAULT_SERVER, tunnel_id: Optional[str] = None):
        self.dns_server = dns_server
        self.tunnel_id = tunnel_id or self._generate_tunnel_id()
        self._sent_chunks: List[str] = []
        self._received: Optional[bytes] = None

    @staticmethod
    def _generate_tunnel_id() -> str:
        seed = f"{time.time()}-{os.getpid()}"
        return hashlib.md5(seed.encode(), usedforsecurity=False).hexdigest()[:16]

    def chunk_data(self, data: bytes) -> List[str]:
        encoded = base64.urlsafe_b64encode(data).decode().rstrip("=")
        return [encoded[i : i + self.CHUNK_SIZE] for i in range(0, len(encoded), self.CHUNK_SIZE)]

    def build_query_name(self, chunk: str, direction: str = "send") -> str:
        label = chunk.replace("_", "-")
        return f"{label}.{direction}.{self.tunnel_id}.tunnel.phoenix"

    def send_data(self, data: bytes, transport: Optional[Any] = None) -> bool:
        """Send data; uses `transport(chunk, query_name)` when provided (for tests)."""
        chunks = self.chunk_data(data)
        success = True
        for chunk in chunks:
            query = self.build_query_name(chunk)
            if transport:
                ok = transport(chunk, query)
            else:
                ok = self._send_chunk_http(chunk, query)
            if ok:
                self._sent_chunks.append(chunk)
            else:
                success = False
                break
        return success

    def _send_chunk_http(self, chunk: str, query_name: str) -> bool:
        try:
            import requests
        except ImportError:
            return False
        try:
            response = requests.get(
                self.dns_server,
                params={"name": query_name, "type": "TXT"},
                headers={"Accept": "application/dns-json"},
                timeout=5,
            )
            return response.status_code == 200
        except requests.RequestException:
            return False

    def receive_data(self, payload: Optional[bytes] = None) -> Optional[bytes]:
        if payload is not None:
            self._received = payload
            return payload
        return self._received

    def generate_config(self) -> Dict[str, Any]:
        return {
            "protocol": "doh_tunnel",
            "dns_server": self.dns_server,
            "tunnel_id": self.tunnel_id,
            "chunk_size": self.CHUNK_SIZE,
            "sent_chunks": len(self._sent_chunks),
        }
