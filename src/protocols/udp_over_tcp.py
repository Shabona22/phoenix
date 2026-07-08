"""UDP-over-TCP wrapper for UDP-blocked networks."""

from typing import Any, Dict

from .base import ProtocolBase


class UdpOverTcpConfig(ProtocolBase):
    def __init__(self):
        super().__init__("UDP-over-TCP", "1.0")

    def generate_config(self, server_ip: str, port: int = None, **kwargs) -> Dict[str, Any]:
        if not port:
            port = self._generate_random_port(10000, 65000)
        backend_port = kwargs.get("backend_port", 51820)
        return {
            "protocol": "udp_over_tcp",
            "server": {"ip": server_ip, "port": port, "proto": "tcp"},
            "backend": {
                "protocol": kwargs.get("backend_protocol", "wireguard"),
                "port": backend_port,
            },
            "mux": {
                "enabled": True,
                "concurrency": kwargs.get("concurrency", 8),
                "padding": True,
            },
        }

    def generate_client_config(self, config: Dict[str, Any]) -> str:
        return f"""# UDP-over-TCP tunnel
server {config['server']['ip']} {config['server']['port']}
backend {config['backend']['protocol']} 127.0.0.1:{config['backend']['port']}
mux concurrency {config['mux']['concurrency']}
"""
