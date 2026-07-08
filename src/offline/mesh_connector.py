"""Offline mesh connectors for total-blackout scenarios.

Two connectors:
- MeshConnector: Bluetooth mesh scaffold (native OS APIs required).
- MeshP2P: local-network TCP peer exchange for sharing configs when the wider
  internet is down. Sockets are only opened via explicit start_server().
"""

from __future__ import annotations

import json
import platform
import socket
import threading
from typing import Callable, Dict, List, Optional


class MeshConnector:
    """OS-level Bluetooth mesh is not available in headless Python; config scaffold only."""

    def __init__(self, device_name: str = "phoenix-mesh"):
        self.device_name = device_name
        self._connected = False

    @property
    def platform(self) -> str:
        return platform.system()

    def generate_config(self, payload: Optional[Dict[str, object]] = None) -> Dict[str, object]:
        return {
            "enabled": False,
            "device_name": self.device_name,
            "platform": self.platform,
            "note": "Bluetooth mesh requires native OS APIs; enable manually on supported devices.",
            "payload_size_limit": 512,
            "payload_preview": json.dumps(payload or {})[:128],
        }

    def connect(self) -> bool:
        self._connected = False
        return False

    def disconnect(self) -> None:
        self._connected = False


class MeshP2P:
    """LAN peer-to-peer config exchange over TCP.

    Designed for full-internet-blackout conditions: peers on the same local
    network can request/share working VPN configs. No socket binds until
    start_server() is called, keeping the class import- and test-safe.
    """

    def __init__(self, local_port: int = 8080):
        self.local_port = local_port
        self.peers: List[str] = []
        self.is_running = False
        self._server: Optional[socket.socket] = None
        self._thread: Optional[threading.Thread] = None
        self._config_provider: Callable[[], Dict[str, object]] = lambda: {}
        self.received: List[Dict[str, object]] = []

    def set_config_provider(self, provider: Callable[[], Dict[str, object]]) -> None:
        self._config_provider = provider

    def add_peer(self, ip: str) -> None:
        if ip not in self.peers:
            self.peers.append(ip)

    def discover_peers(self, candidates: Optional[List[str]] = None) -> List[str]:
        """Register reachable peers. Accepts an explicit candidate list for tests
        and controlled environments; real discovery would scan the local subnet."""
        for ip in candidates or []:
            self.add_peer(ip)
        return list(self.peers)

    def build_message(self, msg_type: str, data: Optional[Dict[str, object]] = None) -> bytes:
        return json.dumps({"type": msg_type, "data": data or {}}).encode()

    def handle_message(self, peer_ip: str, raw: bytes) -> Dict[str, object]:
        """Pure message handler (no I/O) so behavior is unit-testable."""
        try:
            msg = json.loads(raw.decode())
        except (ValueError, UnicodeDecodeError):
            return {"type": "error", "data": {"reason": "malformed"}}

        kind = msg.get("type")
        if kind == "ping":
            return {"type": "pong", "data": {}}
        if kind == "config_request":
            return {"type": "config", "data": self._config_provider()}
        if kind == "config":
            self.received.append({"peer": peer_ip, "config": msg.get("data", {})})
            return {"type": "ack", "data": {}}
        return {"type": "error", "data": {"reason": "unknown_type"}}

    def start_server(self) -> None:
        if self.is_running:
            return
        self.is_running = True
        self._thread = threading.Thread(target=self._serve, daemon=True)
        self._thread.start()

    def _serve(self) -> None:
        self._server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._server.settimeout(1.0)
        self._server.bind(("0.0.0.0", self.local_port))
        self._server.listen(5)
        while self.is_running:
            try:
                conn, addr = self._server.accept()
            except socket.timeout:
                continue
            except OSError:
                break
            with conn:
                data = conn.recv(4096)
                if data:
                    reply = self.handle_message(addr[0], data)
                    conn.sendall(json.dumps(reply).encode())

    def stop(self) -> None:
        self.is_running = False
        if self._server:
            try:
                self._server.close()
            except OSError:
                pass
            self._server = None

    def generate_config(self) -> Dict[str, object]:
        return {
            "enabled": True,
            "mode": "lan_p2p",
            "local_port": self.local_port,
            "peers": list(self.peers),
            "note": "Activates on full internet blackout; shares configs over LAN.",
        }
