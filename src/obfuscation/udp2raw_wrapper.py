"""udp2raw wrapper configuration for UDP-in-TCP camouflage."""

from __future__ import annotations

from typing import Dict


class Udp2RawWrapper:
    def __init__(self, local_port: int = 51820, remote_port: int = 443, cipher: str = "aes128cbc"):
        self.local_port = local_port
        self.remote_port = remote_port
        self.cipher = cipher

    def generate_config(self, server_ip: str) -> Dict[str, object]:
        return {
            "enabled": True,
            "binary": "udp2raw",
            "server_ip": server_ip,
            "local_port": self.local_port,
            "remote_port": self.remote_port,
            "cipher": self.cipher,
            "raw_mode": "udp",
            "auth": True,
            "command": (
                f"udp2raw -s -l0.0.0.0:{self.local_port} -r {server_ip}:{self.remote_port} "
                f"-k phoenix --raw-mode udp -a"
            ),
        }
