"""ICMP tunnel scaffold — fallback channel when SSH/TCP paths are blocked.

Real ICMP tunneling needs raw sockets and root/CAP_NET_RAW, which are unavailable
in most sandboxes. This module provides capability detection, packet framing
helpers, and a deployable config so the rest of the system can reason about it.
"""

from __future__ import annotations

import os
import struct
from typing import Any, Dict

ICMP_ECHO_REQUEST = 8
MAX_PAYLOAD = 1400


class ICMPTunnel:
    def __init__(self, server_ip: str, identifier: int = 0xC0DE):
        self.server_ip = server_ip
        self.identifier = identifier & 0xFFFF
        self._seq = 0

    @staticmethod
    def available() -> bool:
        """Raw ICMP sockets require elevated privileges."""
        if os.name != "posix":
            return False
        try:
            return os.geteuid() == 0
        except AttributeError:
            return False

    @staticmethod
    def _checksum(data: bytes) -> int:
        if len(data) % 2:
            data += b"\x00"
        total = 0
        for i in range(0, len(data), 2):
            total += (data[i] << 8) + data[i + 1]
        total = (total >> 16) + (total & 0xFFFF)
        total += total >> 16
        return (~total) & 0xFFFF

    def build_packet(self, payload: bytes) -> bytes:
        """Frame a payload into an ICMP echo-request packet."""
        if len(payload) > MAX_PAYLOAD:
            raise ValueError(f"payload exceeds {MAX_PAYLOAD} bytes")
        self._seq = (self._seq + 1) & 0xFFFF
        header = struct.pack("!BBHHH", ICMP_ECHO_REQUEST, 0, 0, self.identifier, self._seq)
        chksum = self._checksum(header + payload)
        header = struct.pack("!BBHHH", ICMP_ECHO_REQUEST, 0, chksum, self.identifier, self._seq)
        return header + payload

    def generate_config(self) -> Dict[str, Any]:
        return {
            "protocol": "icmp_tunnel",
            "role": "backup_of_ssh",
            "server": {"ip": self.server_ip},
            "identifier": self.identifier,
            "max_payload": MAX_PAYLOAD,
            "available": self.available(),
            "note": "Requires root/CAP_NET_RAW; enable only on a controlled endpoint.",
        }
