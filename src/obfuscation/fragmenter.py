"""Packet fragmentation helper for DPI evasion."""

from __future__ import annotations

from typing import List


class Fragmenter:
    def __init__(self, chunk_size: int = 512):
        self.chunk_size = max(64, chunk_size)

    def fragment(self, payload: bytes) -> List[bytes]:
        if not payload:
            return []
        return [payload[i : i + self.chunk_size] for i in range(0, len(payload), self.chunk_size)]

    def reassemble(self, chunks: List[bytes]) -> bytes:
        return b"".join(chunks)

    def generate_config(self) -> dict:
        return {"enabled": True, "chunk_size": self.chunk_size}
