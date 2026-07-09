"""Unit tests for Auto-Adapt HTTP2/WS protocol configs."""

from protocols.l2tp_websocket import L2TPWebSocketConfig
from protocols.openvpn_http2 import OpenVPNHttp2Config
from protocols.wireguard_http2 import WireGuardHttp2Config


def test_openvpn_http2_config():
    cfg = OpenVPNHttp2Config().generate_config("93.114.98.9")
    assert cfg["protocol"] == "openvpn_http2"
    assert cfg["tls"]["alpn"] == "h2"
    assert cfg["server"]["port"] == 443
    client = OpenVPNHttp2Config().generate_client_config(cfg)
    assert "ALPN h2" in client or "ALPN" in client


def test_l2tp_websocket_config():
    cfg = L2TPWebSocketConfig().generate_config("93.114.98.9")
    assert cfg["protocol"] == "l2tp_websocket"
    assert cfg["tunnel"]["type"] == "xray_websocket"
    assert cfg["tunnel"]["xray_config"]["streamSettings"]["network"] == "ws"


def test_wireguard_http2_config():
    cfg = WireGuardHttp2Config().generate_config("1.2.3.4")
    assert cfg["protocol"] == "wireguard_http2"
    assert cfg["transport"]["type"] == "http2"
    assert "inner_port" in cfg["wireguard"]
