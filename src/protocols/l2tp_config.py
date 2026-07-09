import secrets
from typing import Any, Dict

from .base import ProtocolBase


class L2TPConfig(ProtocolBase):
    def __init__(self):
        super().__init__("L2TP/IPSec", "1.0")

    def generate_config(self, server_ip: str, psk: str = None, **kwargs) -> Dict[str, Any]:
        if not psk:
            psk = secrets.token_hex(20)
        username = kwargs.get("username", f"user_{secrets.token_hex(4)}")
        password = kwargs.get("password", self._generate_password(16))
        return {
            "protocol": "l2tp_ipsec",
            "server": {"ip": server_ip, "ipsec_port": 4500, "l2tp_port": 1701},
            "ipsec": {
                "phase1": {"algorithm": "aes256-sha256-modp2048", "lifetime": "28800s"},
                "phase2": {"algorithm": "aes256-sha256", "lifetime": "3600s"},
                "pre_shared_key": psk,
                "nat_traversal": True,
            },
            "auth": {
                "username": username,
                "password": password,
            },
            "network": {
                "local_ip": "192.168.42.1",
                "ip_range": "192.168.42.10-192.168.42.50",
            },
        }

    def generate_client_config(self, config: Dict[str, Any]) -> str:
        return f"""L2TP/IPSec PSK
Server: {config['server']['ip']}
PSK: {config['ipsec']['pre_shared_key']}
Username: {config['auth']['username']}
Password: {config['auth']['password']}
NAT Traversal: Enabled
"""

    def generate_server_config(self, config: Dict[str, Any]) -> str:
        """Return combined server files as marked sections for bootstrap to split."""
        ipsec = f"""config setup
    charondebug="ike 1, knl 1, cfg 0"
    uniqueids=no

conn l2tp-psk
    auto=add
    keyexchange=ikev1
    authby=secret
    type=transport
    left=%defaultroute
    leftprotoport=17/1701
    right=%any
    rightprotoport=17/%any
    ike={config['ipsec']['phase1']['algorithm']}!
    esp={config['ipsec']['phase2']['algorithm']}!
    keyingtries=3
    ikelifetime={config['ipsec']['phase1']['lifetime']}
    lifetime={config['ipsec']['phase2']['lifetime']}
    dpdaction=clear
    dpddelay=30
"""
        xl2tpd = f"""[global]
listen-addr = 0.0.0.0
port = {config['server']['l2tp_port']}

[lns default]
ip range = {config['network']['ip_range']}
local ip = {config['network']['local_ip']}
require authentication = yes
name = phoenix-l2tp
ppp debug = no
pppoptfile = /etc/ppp/options.xl2tpd
length bit = yes
"""
        secrets = f"""# ipsec.secrets
%any %any : PSK "{config['ipsec']['pre_shared_key']}"

# chap-secrets
"{config['auth']['username']}" * "{config['auth']['password']}" *
"""
        return f"### ipsec.conf\n{ipsec}\n### xl2tpd.conf\n{xl2tpd}\n### secrets\n{secrets}"
