"""SSH SOCKS tunnel as a last-resort circumvention channel.

Network operations are explicit; nothing connects at import or construction time
so the module stays testable without paramiko, credentials, or a live server.
"""

from __future__ import annotations

import threading
from typing import Any, Dict, Optional


class SSHTunnel:
    """Maintain a persistent SOCKS tunnel over SSH.

    paramiko is imported lazily so the class can be constructed and configured
    (and its config serialized) even when paramiko is not installed.
    """

    def __init__(
        self,
        server_ip: str,
        username: str,
        password: Optional[str] = None,
        key_file: Optional[str] = None,
        ssh_port: int = 22,
    ):
        self.server_ip = server_ip
        self.username = username
        self.password = password
        self.key_file = key_file
        self.ssh_port = ssh_port
        self.client: Any = None
        self._thread: Optional[threading.Thread] = None
        self.is_running = False
        self.last_error: Optional[str] = None

    @staticmethod
    def available() -> bool:
        try:
            import paramiko  # noqa: F401

            return True
        except ImportError:
            return False

    def connect(self, timeout: int = 10) -> bool:
        try:
            import paramiko
        except ImportError:
            self.last_error = "paramiko not installed"
            return False

        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            kwargs: Dict[str, Any] = {
                "hostname": self.server_ip,
                "port": self.ssh_port,
                "username": self.username,
                "timeout": timeout,
                "allow_agent": False,
                "look_for_keys": False,
            }
            if self.key_file:
                kwargs["key_filename"] = self.key_file
            else:
                kwargs["password"] = self.password
            client.connect(**kwargs)
            self.client = client
            self.last_error = None
            return True
        except Exception as exc:  # noqa: BLE001 - report, don't crash the healer
            self.last_error = str(exc)
            return False

    def is_connected(self) -> bool:
        transport = self.client.get_transport() if self.client else None
        return bool(transport and transport.is_active())

    def start_persistent(self, local_port: int = 10808, check_interval: int = 60) -> None:
        """Spawn a daemon thread that keeps the SSH channel alive."""
        if self.is_running:
            return
        self.is_running = True
        self._thread = threading.Thread(
            target=self._loop, args=(local_port, check_interval), daemon=True
        )
        self._thread.start()

    def _loop(self, local_port: int, check_interval: int) -> None:
        while self.is_running:
            if not self.is_connected():
                self.connect()
            self._reap(check_interval)

    def _reap(self, seconds: int) -> None:
        # Interruptible sleep so stop() takes effect quickly.
        waited = 0.0
        while self.is_running and waited < seconds:
            threading.Event().wait(0.5)
            waited += 0.5

    def stop(self) -> None:
        self.is_running = False
        if self.client:
            try:
                self.client.close()
            except Exception:  # noqa: BLE001
                pass
            self.client = None

    def generate_config(self, local_port: int = 10808) -> Dict[str, Any]:
        return {
            "protocol": "ssh_tunnel",
            "role": "last_resort",
            "server": {"ip": self.server_ip, "port": self.ssh_port},
            "username": self.username,
            "auth": "key" if self.key_file else "password",
            "socks": {"host": "127.0.0.1", "port": local_port, "type": "socks5"},
            "keepalive_seconds": 60,
            "paramiko_available": self.available(),
        }
