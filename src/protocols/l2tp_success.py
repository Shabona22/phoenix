"""L2TP success profile (Esfand 1404 field-tested)."""

from __future__ import annotations

import secrets
from typing import Any, Dict

from protocols.base import ProtocolBase


class L2TPSuccessConfig(ProtocolBase):
    """L2TP/IPsec with IKEv2 + AES-256 + NAT-T."""

    def __init__(self) -> None:
        super().__init__("L2TP-Success", "1.0")

    def generate_config(self, server_ip: str, **kwargs: Any) -> Dict[str, Any]:
        psk = secrets.token_hex(20)
        username = kwargs.get("username", f"user_{secrets.token_hex(4)}")
        password = kwargs.get("password", self._generate_password(16))
        return {
            "protocol": "l2tp_success",
            "server": {"ip": server_ip, "ipsec_port": 4500, "l2tp_port": 1701},
            "ipsec": {
                "phase1": {
                    "algorithm": "aes256-sha256-modp2048",
                    "lifetime": "28800s",
                    "dh_group": 14,
                },
                "phase2": {
                    "algorithm": "aes256-sha256",
                    "lifetime": "3600s",
                    "pfs": "yes",
                },
                "pre_shared_key": psk,
                "nat_traversal": True,
                "force_encaps": True,
            },
            "auth": {"username": username, "password": password},
            "dynamic": {"psk_rotation": True, "port_rotation": True},
        }

    def generate_client_config(self, config: Dict[str, Any]) -> str:
        server = config["server"]
        auth = config["auth"]
        return f"""L2TP/IPsec (IKEv2)
Server: {server['ip']}
L2TP Port: {server['l2tp_port']}
IPsec Port: {server['ipsec_port']}
Username: {auth['username']}
Password: {auth['password']}
"""

    def generate_server_config(self, config: Dict[str, Any]) -> str:
        return self.generate_strongswan_config(config)

    def generate_strongswan_config(self, config: Dict[str, Any]) -> str:
        ipsec = config["ipsec"]
        return f"""config setup
    charondebug="all"
    uniqueids=yes
conn %default
    ikelifetime={ipsec['phase1']['lifetime']}
    keylife={ipsec['phase2']['lifetime']}
    rekeymargin=3m
    keyingtries=1
    keyexchange=ikev2
    authby=secret
    type=transport
    leftprotoport=udp/l2tp
    rightprotoport=udp/%any
    forceencaps=yes
conn l2tp
    left=%any
    leftid=@localhost
    right={config['server']['ip']}
    auto=add
    esp={ipsec['phase2']['algorithm']}
    ike={ipsec['phase1']['algorithm']}
    ikelifetime={ipsec['phase1']['lifetime']}
    lifetime={ipsec['phase2']['lifetime']}
"""
