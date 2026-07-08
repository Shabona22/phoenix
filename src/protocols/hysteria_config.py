from typing import Any, Dict

from .base import ProtocolBase


class HysteriaConfig(ProtocolBase):
    def __init__(self):
        super().__init__("Hysteria", "2.0")

    def generate_config(self, server_ip: str, port: int = None, **kwargs) -> Dict[str, Any]:
        if not port:
            port = self._generate_random_port(10000, 65000)
        return {
            "protocol": "hysteria",
            "server": {"ip": server_ip, "port": port, "proto": "udp"},
            "auth": {
                "type": "password",
                "password": kwargs.get("password", self._generate_password(20)),
            },
            "obfuscation": {
                "type": "salamander",
                "password": kwargs.get("obfs_password", self._generate_password(16)),
            },
            "tls": {
                "enabled": True,
                "sni": kwargs.get("sni", "www.bing.com"),
                "insecure": False,
            },
            "quic": {
                "init_stream_receive_window": 8388608,
                "max_stream_receive_window": 8388608,
                "init_conn_receive_window": 20971520,
                "max_conn_receive_window": 20971520,
            },
        }

    def generate_client_config(self, config: Dict[str, Any]) -> str:
        return f"""server: {config['server']['ip']}:{config['server']['port']}
auth: {config['auth']['password']}
obfs: {config['obfuscation']['password']}
sni: {config['tls']['sni']}
protocol: udp
"""
