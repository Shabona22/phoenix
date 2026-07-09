#!/usr/bin/env python3
"""Generate RouterOS scripts for MikroTik hap ax3."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class MikroTikSettings:
    wan1_gateway: str = "192.168.1.1"
    wan2_gateway: str = "192.168.2.1"
    internal_gateway: str = "192.168.1.1"
    external_gateway: str = "wg-server"
    wg_private_key: str = ""
    wg_public_key: str = ""
    wg_server_address: str = "10.0.0.1/24"
    wg_peer_address: str = "10.0.0.2/32"
    l2tp_psk: str = ""
    syslog_host: str = "192.168.88.10"
    mesh_ssid: str = "phoenix-mesh"
    hap_model: str = "hap_ax3"
    wifi_interface: str = "wifi1"

    @classmethod
    def from_env(cls) -> "MikroTikSettings":
        return cls(
            wan1_gateway=os.getenv("MIKROTIK_WAN1_GATEWAY", "192.168.1.1"),
            wan2_gateway=os.getenv("MIKROTIK_WAN2_GATEWAY", "192.168.2.1"),
            internal_gateway=os.getenv("MIKROTIK_INTERNAL_GATEWAY", "192.168.1.1"),
            external_gateway=os.getenv("MIKROTIK_EXTERNAL_GATEWAY", "wg-server"),
            wg_private_key=os.getenv("MIKROTIK_WG_PRIVATE_KEY", ""),
            wg_public_key=os.getenv("MIKROTIK_WG_PUBLIC_KEY", ""),
            wg_server_address=os.getenv("MIKROTIK_WG_SERVER_ADDRESS", "10.0.0.1/24"),
            wg_peer_address=os.getenv("MIKROTIK_WG_PEER_ADDRESS", "10.0.0.2/32"),
            l2tp_psk=os.getenv("MIKROTIK_L2TP_PSK", ""),
            syslog_host=os.getenv("PHOENIX_SYSLOG_HOST", "192.168.88.10"),
            mesh_ssid=os.getenv("MIKROTIK_MESH_SSID", "phoenix-mesh"),
            hap_model=os.getenv("MIKROTIK_HAP_MODEL", "hap_ax3"),
            wifi_interface=os.getenv("MIKROTIK_WIFI_INTERFACE", "wifi1"),
        )

    @classmethod
    def from_json_file(cls, path: str) -> "MikroTikSettings":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        base = cls.from_env()
        for key, value in data.items():
            if hasattr(base, key):
                setattr(base, key, value)
        return base


SCRIPT_ORDER = [
    "dns_cache",
    "smart_splitter",
    "multi_wan",
    "smart_firewall",
    "vpn_server",
    "mesh_client",
    "monitoring",
]


class MikroTikConfigGenerator:
    def __init__(
        self,
        settings: Optional[MikroTikSettings] = None,
        scripts_dir: Optional[str] = None,
        root: Optional[Path] = None,
    ) -> None:
        self.root = root or Path(__file__).resolve().parent.parent.parent
        self.scripts_dir = Path(scripts_dir or self.root / "scripts" / "mikrotik")
        config_path = os.getenv("PHOENIX_MIKROTIK_CONFIG")
        if settings:
            self.settings = settings
        elif config_path and Path(config_path).is_file():
            self.settings = MikroTikSettings.from_json_file(config_path)
        else:
            self.settings = MikroTikSettings.from_env()

    def generate_all_scripts(self) -> Dict[str, str]:
        scripts = {
            "smart_splitter": self._generate_smart_splitter(),
            "dns_cache": self._generate_dns_cache(),
            "multi_wan": self._generate_multi_wan(),
            "smart_firewall": self._generate_smart_firewall(),
            "mesh_client": self._generate_mesh_client(),
            "vpn_server": self._generate_vpn_server(),
            "monitoring": self._generate_monitoring(),
        }
        self.scripts_dir.mkdir(parents=True, exist_ok=True)
        for name, content in scripts.items():
            (self.scripts_dir / f"{name}.rsc").write_text(content.strip() + "\n", encoding="utf-8")
        return scripts

    def generate_script(self, name: str) -> str:
        generators = {
            "smart_splitter": self._generate_smart_splitter,
            "dns_cache": self._generate_dns_cache,
            "multi_wan": self._generate_multi_wan,
            "smart_firewall": self._generate_smart_firewall,
            "mesh_client": self._generate_mesh_client,
            "vpn_server": self._generate_vpn_server,
            "monitoring": self._generate_monitoring,
        }
        if name not in generators:
            raise ValueError(f"Unknown script: {name}")
        content = generators[name]()
        self.scripts_dir.mkdir(parents=True, exist_ok=True)
        (self.scripts_dir / f"{name}.rsc").write_text(content.strip() + "\n", encoding="utf-8")
        return content

    def list_script_paths(self) -> List[Path]:
        return sorted(self.scripts_dir.glob("*.rsc"))

    def _header(self, title: str) -> str:
        return f"# {title}\n# Phoenix V10 MikroTik Ready – {self.settings.hap_model}\n:log info \"phoenix: applying {title}\""

    def _generate_smart_splitter(self) -> str:
        s = self.settings
        return f"""
{self._header("Smart Splitter")}
:do {{ /ip firewall address-list add list=Iran_IPs address=10.0.0.0/8 }} on-error={{}}
:do {{ /ip firewall address-list add list=Iran_IPs address=172.16.0.0/12 }} on-error={{}}
:do {{ /ip firewall address-list add list=Iran_IPs address=192.168.0.0/16 }} on-error={{}}
:do {{ /ip firewall mangle add chain=prerouting dst-address-list=Iran_IPs action=mark-routing new-routing-mark=internal passthrough=yes comment=phoenix-internal }} on-error={{}}
:do {{ /ip firewall mangle add chain=prerouting dst-address-list=!Iran_IPs action=mark-routing new-routing-mark=external passthrough=yes comment=phoenix-external }} on-error={{}}
:do {{ /ip route add routing-mark=internal gateway={s.internal_gateway} comment=phoenix-internal-route }} on-error={{}}
:do {{ /ip route add routing-mark=external gateway={s.external_gateway} comment=phoenix-external-route }} on-error={{}}
:do {{ /system logging add topics=firewall action=memory }} on-error={{}}
:log info "phoenix: smart_splitter done"
"""

    def _generate_dns_cache(self) -> str:
        return f"""
{self._header("DNS Cache")}
/ip dns set servers=1.1.1.1,8.8.8.8 allow-remote-requests=yes cache-size=2048KiB
/ip dns cache flush
:do {{ /ip dns static add name=google.com address=142.250.185.78 }} on-error={{}}
:do {{ /ip dns static add name=github.com address=140.82.121.3 }} on-error={{}}
:do {{ /ip dns static add name=cloudflare.com address=104.16.124.96 }} on-error={{}}
:do {{ /system logging add topics=dns action=memory }} on-error={{}}
:log info "phoenix: dns_cache done"
"""

    def _generate_multi_wan(self) -> str:
        s = self.settings
        return f"""
{self._header("Multi-WAN")}
:do {{ /interface pppoe-client add interface=ether1 user=user1 password=pass1 name=wan1 disabled=no }} on-error={{}}
:do {{ /interface pppoe-client add interface=ether2 user=user2 password=pass2 name=wan2 disabled=no }} on-error={{}}
:do {{ /ip route add gateway=wan1 check-gateway=ping distance=1 comment=phoenix-wan1 }} on-error={{}}
:do {{ /ip route add gateway=wan2 check-gateway=ping distance=2 comment=phoenix-wan2 }} on-error={{}}
:do {{ /ip firewall mangle add chain=prerouting dst-address-type=!local in-interface=bridge action=mark-connection new-connection-mark=wan1-conn per-connection-classifier=src-address-and-port:2/0 passthrough=yes comment=phoenix-pcc-wan1 }} on-error={{}}
:do {{ /ip firewall mangle add chain=prerouting dst-address-type=!local in-interface=bridge action=mark-connection new-connection-mark=wan2-conn per-connection-classifier=src-address-and-port:2/1 passthrough=yes comment=phoenix-pcc-wan2 }} on-error={{}}
:do {{ /ip route add gateway={s.wan1_gateway} routing-mark=wan1-conn comment=phoenix-wan1-pcc }} on-error={{}}
:do {{ /ip route add gateway={s.wan2_gateway} routing-mark=wan2-conn comment=phoenix-wan2-pcc }} on-error={{}}
:do {{ /system logging add topics=firewall action=memory }} on-error={{}}
:log info "phoenix: multi_wan done"
"""

    def _generate_smart_firewall(self) -> str:
        return f"""
{self._header("Smart Firewall")}
:do {{ /ip firewall filter add chain=input protocol=tcp tcp-flags=syn connection-limit=10,32 action=drop comment=phoenix-syn-flood }} on-error={{}}
:do {{ /ip firewall filter add chain=input protocol=icmp icmp-options=8:0 limit=5,5 action=accept comment=phoenix-icmp-limit }} on-error={{}}
:do {{ /ip firewall filter add chain=input protocol=tcp psd=21,3s,3,1 action=drop comment=phoenix-port-scan }} on-error={{}}
:do {{ /ip firewall address-list add list=blacklist address=1.2.3.4 comment=phoenix-blacklist-example }} on-error={{}}
:do {{ /ip firewall filter add chain=input src-address-list=blacklist action=drop comment=phoenix-blacklist-drop }} on-error={{}}
:do {{ /system logging add topics=firewall action=memory }} on-error={{}}
:log info "phoenix: smart_firewall done"
"""

    def _generate_mesh_client(self) -> str:
        s = self.settings
        return f"""
{self._header("Mesh Client")}
# hap ax3 uses wifiwave2; interface name may be {s.wifi_interface}
:do {{ /interface wifi set [find default-name={s.wifi_interface}] disabled=no ssid="{s.mesh_ssid}" }} on-error={{}}
:do {{ /ip route add dst-address=192.168.200.0/24 gateway={s.wifi_interface} comment=phoenix-mesh-route }} on-error={{}}
:do {{ /system logging add topics=wireless action=memory }} on-error={{}}
:log info "phoenix: mesh_client done"
"""

    def _generate_vpn_server(self) -> str:
        s = self.settings
        wg_key = s.wg_private_key or "REPLACE_WG_PRIVATE_KEY"
        peer_key = s.wg_public_key or "REPLACE_WG_PUBLIC_KEY"
        psk = s.l2tp_psk or "REPLACE_L2TP_PSK"
        return f"""
{self._header("VPN Server")}
:do {{ /interface wireguard add name=wg-server private-key="{wg_key}" comment=phoenix-wg }} on-error={{}}
:do {{ /ip address add address={s.wg_server_address} interface=wg-server }} on-error={{}}
:do {{ /interface wireguard peers add interface=wg-server public-key="{peer_key}" allowed-address={s.wg_peer_address} comment=phoenix-wg-peer }} on-error={{}}
:do {{ /ppp profile add name=l2tp-profile local-address=192.168.100.1 remote-address=192.168.100.2-192.168.100.254 }} on-error={{}}
/interface l2tp-server server set enabled=yes default-profile=l2tp-profile
/ip ipsec proposal set [ find default=yes ] enc-algorithms=aes-256-cbc
:do {{ /ip ipsec peer add address=0.0.0.0/0 passive=yes }} on-error={{}}
:do {{ /ip ipsec identity add peer=0.0.0.0/0 auth-method=pre-shared-key secret="{psk}" }} on-error={{}}
/interface ovpn-server server set enabled=yes port=1194 mode=tcp
:do {{ /system logging add topics=wireguard action=memory }} on-error={{}}
:log info "phoenix: vpn_server done"
"""

    def _generate_monitoring(self) -> str:
        s = self.settings
        return f"""
{self._header("Monitoring")}
:do {{ /system logging action add name=phoenix target=remote remote={s.syslog_host} port=514 }} on-error={{}}
:do {{ /system logging add topics=info action=phoenix }} on-error={{}}
:do {{ /system logging add topics=error action=phoenix }} on-error={{}}
:do {{ /system logging add topics=wireguard action=phoenix }} on-error={{}}
:do {{ /system logging add topics=firewall action=phoenix }} on-error={{}}
:do {{ /tool graphing interface add interface=all }} on-error={{}}
:log info "phoenix: monitoring done"
"""
