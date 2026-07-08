"""Unit tests for OpenVPN and L2TP configs."""

from protocols.l2tp_config import L2TPConfig
from protocols.openvpn_config import OpenVPNConfig


def test_openvpn_generates_config():
    ovpn = OpenVPNConfig()
    cfg = ovpn.generate_config("1.2.3.4", port=1194)
    assert cfg["protocol"] == "openvpn"
    assert cfg["server"]["ip"] == "1.2.3.4"
    assert cfg["server"]["port"] == 1194
    assert cfg["obfuscation"]["enabled"] is True
    client = ovpn.generate_client_config(cfg)
    assert "remote 1.2.3.4 1194" in client
    assert "tls-crypt-v2" in client


def test_l2tp_generates_config():
    l2tp = L2TPConfig()
    cfg = l2tp.generate_config("5.6.7.8", psk="abc123")
    assert cfg["protocol"] == "l2tp_ipsec"
    assert cfg["ipsec"]["pre_shared_key"] == "abc123"
    assert cfg["server"]["l2tp_port"] == 1701
    client = l2tp.generate_client_config(cfg)
    assert "5.6.7.8" in client
    assert "abc123" in client
