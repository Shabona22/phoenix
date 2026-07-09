"""Unit tests for MikroTikConfigGenerator."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from mikrotik.advanced_config_generator import MikroTikConfigGenerator, MikroTikSettings, SCRIPT_ORDER


@pytest.fixture
def tmp_generator(tmp_path):
    return MikroTikConfigGenerator(
        settings=MikroTikSettings(
            wan1_gateway="10.0.0.1",
            wan2_gateway="10.0.0.2",
            internal_gateway="192.168.1.1",
            external_gateway="wg-server",
            wg_private_key="test-priv",
            wg_public_key="test-pub",
            l2tp_psk="test-psk",
            syslog_host="10.0.0.50",
            mesh_ssid="test-mesh",
        ),
        scripts_dir=str(tmp_path / "scripts"),
        root=tmp_path,
    )


def test_generate_all_scripts_creates_seven_files(tmp_generator, tmp_path):
    scripts = tmp_generator.generate_all_scripts()
    assert len(scripts) == 7
    for name in scripts:
        assert (tmp_path / "scripts" / f"{name}.rsc").is_file()


def test_script_order_matches_plan():
    assert SCRIPT_ORDER[0] == "dns_cache"
    assert SCRIPT_ORDER[-1] == "monitoring"
    assert len(SCRIPT_ORDER) == 7


def test_smart_splitter_contains_gateways(tmp_generator):
    content = tmp_generator._generate_smart_splitter()
    assert "192.168.1.1" in content
    assert "wg-server" in content
    assert "Iran_IPs" in content


def test_dns_cache_contains_cache_size(tmp_generator):
    content = tmp_generator._generate_dns_cache()
    assert "cache-size=2048KiB" in content
    assert "google.com" in content


def test_multi_wan_contains_pcc(tmp_generator):
    content = tmp_generator._generate_multi_wan()
    assert "per-connection-classifier" in content
    assert "10.0.0.1" in content


def test_smart_firewall_contains_syn_flood(tmp_generator):
    content = tmp_generator._generate_smart_firewall()
    assert "connection-limit=10,32" in content
    assert "psd=21,3s,3,1" in content


def test_mesh_client_contains_ssid(tmp_generator):
    content = tmp_generator._generate_mesh_client()
    assert "test-mesh" in content
    assert "wifi1" in content


def test_vpn_server_templates_keys(tmp_generator):
    content = tmp_generator._generate_vpn_server()
    assert "test-priv" in content
    assert "test-pub" in content
    assert "test-psk" in content
    assert "wireguard" in content


def test_monitoring_contains_syslog_host(tmp_generator):
    content = tmp_generator._generate_monitoring()
    assert "10.0.0.50" in content
    assert "port=514" in content


def test_generate_single_script(tmp_generator, tmp_path):
    content = tmp_generator.generate_script("dns_cache")
    assert "dns_cache done" in content
    assert (tmp_path / "scripts" / "dns_cache.rsc").is_file()


def test_unknown_script_raises(tmp_generator):
    with pytest.raises(ValueError, match="Unknown script"):
        tmp_generator.generate_script("nonexistent")


def test_settings_from_json_file(tmp_path, monkeypatch):
    config = tmp_path / "mikrotik.json"
    config.write_text(json.dumps({"mesh_ssid": "from-json", "syslog_host": "1.2.3.4"}))
    monkeypatch.setenv("PHOENIX_MIKROTIK_CONFIG", str(config))
    gen = MikroTikConfigGenerator(scripts_dir=str(tmp_path / "scripts"), root=tmp_path)
    assert gen.settings.mesh_ssid == "from-json"
    assert gen.settings.syslog_host == "1.2.3.4"


def test_scripts_are_idempotent_markers(tmp_generator):
    for name in SCRIPT_ORDER:
        method = getattr(tmp_generator, f"_generate_{name}")
        content = method()
        assert "on-error" in content
        assert "phoenix:" in content
