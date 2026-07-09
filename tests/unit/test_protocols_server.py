"""Unit tests for daemon-ready server configs."""

import json
import re

from protocols.hysteria_config import HysteriaConfig
from protocols.openvpn_config import OpenVPNConfig
from protocols.shadowsocks_config import ShadowsocksConfig
from protocols.wireguard_config import WireGuardConfig
from protocols.xray_config import XrayConfig
from utils.crypto import generate_x25519_reality_keypair


def test_xray_reality_keys_valid_base64url():
    priv, pub = generate_x25519_reality_keypair()
    assert re.fullmatch(r"[A-Za-z0-9_-]+", priv)
    assert re.fullmatch(r"[A-Za-z0-9_-]+", pub)
    assert len(priv) >= 40


def test_xray_server_config_is_valid_json():
    gen = XrayConfig()
    cfg = gen.generate_config("1.2.3.4", port=44333)
    raw = gen.generate_server_config(cfg)
    parsed = json.loads(raw)
    assert parsed["inbounds"][0]["protocol"] == "vless"
    assert parsed["inbounds"][0]["streamSettings"]["security"] == "reality"
    assert "privateKey" in parsed["inbounds"][0]["streamSettings"]["realitySettings"]


def test_hysteria_server_config_has_listen_and_auth():
    gen = HysteriaConfig()
    cfg = gen.generate_config("1.2.3.4", port=8443)
    raw = gen.generate_server_config(cfg)
    assert "listen: :8443" in raw
    assert "auth:" in raw
    assert "salamander:" in raw


def test_shadowsocks_server_config_json():
    gen = ShadowsocksConfig()
    cfg = gen.generate_config("1.2.3.4", port=8388)
    raw = gen.generate_server_config(cfg)
    parsed = json.loads(raw)
    assert parsed["server"] == "0.0.0.0"
    assert parsed["server_port"] == 8388
    assert parsed["method"] == "aes-256-gcm"


def test_wireguard_server_config_has_peer():
    gen = WireGuardConfig()
    cfg = gen.generate_config("1.2.3.4", port=51820)
    raw = gen.generate_server_config(cfg)
    assert "[Interface]" in raw
    assert "[Peer]" in raw
    assert "ListenPort = 51820" in raw
    assert cfg["client_keys"]["public"] in raw


def test_openvpn_server_config_paths():
    gen = OpenVPNConfig()
    cfg = gen.generate_config("1.2.3.4", port=1194)
    raw = gen.generate_server_config(cfg)
    assert "port 1194" in raw
    assert "tls-crypt-v2" in raw
    assert "/opt/phoenix/openvpn" in raw or "/etc/openvpn" in raw or "ca " in raw
