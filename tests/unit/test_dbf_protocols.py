"""Unit tests for no-TLS and DBF protocol configs."""

from protocols.no_tls.http_upgrade import HTTPUpgradeConfig
from protocols.no_tls.tcp_plain import TCPPlainConfig
from protocols.no_tls.websocket_plain import WebSocketPlainConfig
from protocols.openvpn_cloak import OpenVPNCloakConfig
from protocols.openvpn_success import OpenVPNSuccessConfig
from protocols.l2tp_success import L2TPSuccessConfig
from protocols.wireguard_amnezia import WireGuardAmneziaConfig
from protocols.wireguard_tls import WireGuardTLSConfig
from protocols.xray_reality import XrayRealityConfig


def test_websocket_plain_no_tls():
    cfg_gen = WebSocketPlainConfig()
    cfg = cfg_gen.generate_config("93.114.98.9")
    assert cfg["tls"] is False
    assert cfg["protocol"] == "websocket_plain"
    client = cfg_gen.generate_client_config(cfg)
    assert client.startswith("ws://")


def test_tcp_plain_config():
    cfg_gen = TCPPlainConfig()
    cfg = cfg_gen.generate_config("93.114.98.9", port=12345)
    assert cfg["tls"] is False
    assert cfg["server"]["port"] == 12345


def test_http_upgrade_config():
    cfg_gen = HTTPUpgradeConfig()
    cfg = cfg_gen.generate_config("93.114.98.9")
    assert cfg["network"]["upgrade"] == "websocket"
    assert cfg["tls"] is False


def test_openvpn_cloak_and_amnezia():
    cloak = OpenVPNCloakConfig().generate_config("1.2.3.4")
    amnezia = WireGuardAmneziaConfig().generate_config("1.2.3.4")
    assert cloak["protocol"] == "openvpn_cloak"
    assert amnezia["protocol"] == "wireguard_amnezia"


def test_xray_reality_config():
    cfg = XrayRealityConfig().generate_config("1.2.3.4")
    assert cfg["protocol"] == "xray_reality"
    assert cfg["transport"]["security"] == "reality"


def test_success_technique_protocols():
    ovpn = OpenVPNSuccessConfig().generate_config("1.2.3.4")
    assert ovpn["server"]["port"] == 443
    assert ovpn["tls"]["crypt"] == "tls-crypt-v2"
    l2tp = L2TPSuccessConfig().generate_config("1.2.3.4")
    assert l2tp["ipsec"]["nat_traversal"] is True
    wg = WireGuardTLSConfig().generate_config("1.2.3.4")
    assert wg["tls"]["version"] == "1.3"
