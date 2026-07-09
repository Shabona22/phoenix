"""Unit tests for Auto-Adapt monitoring system."""

import json
from unittest.mock import MagicMock

from healer.fallback_manager import FallbackManager
from monitoring.auto_adapt import AutoAdapt
from monitoring.status_analyzer import StatusAnalyzer
from orchestrator.node_manager import NodeManager


def _make_manager():
    client = MagicMock()
    client.list_vms.return_value = [
        {"vmCode": "vm-1", "sysName": "node-1", "ip": "1.1.1.1", "status": "running"},
    ]
    return NodeManager(client)


def _data_normal() -> dict:
    return {
        "timestamp": 1.0,
        "ping_tests": {"1.1.1.1": {"success": True}},
        "dns_tests": {"google.com": {"success": True}},
        "http_tests": {"google.com": {"success": True, "latency": 30}},
        "user_reports": {},
    }


def _data_moderate() -> dict:
    return {
        "timestamp": 2.0,
        "ping_tests": {"1.1.1.1": {"success": True}},
        "dns_tests": {"google.com": {"success": True}},
        "http_tests": {"google.com": {"success": True, "latency": 180}},
        "user_reports": {},
    }


def _data_severe() -> dict:
    return {
        "timestamp": 3.0,
        "ping_tests": {"1.1.1.1": {"success": True}, "8.8.8.8": {"success": True}},
        "dns_tests": {"google.com": {"success": True}},
        "http_tests": {"google.com": {"success": False}},
        "user_reports": {},
    }


def _data_critical() -> dict:
    return {
        "timestamp": 4.0,
        "ping_tests": {"1.1.1.1": {"success": False}},
        "dns_tests": {"google.com": {"success": False}},
        "http_tests": {"google.com": {"success": False}},
        "user_reports": {},
    }


def test_fallback_starts_with_openvpn_http2():
    fb = FallbackManager(_make_manager())
    assert fb.current_protocol == "openvpn_http2"


def test_status_analyzer_normal():
    status = StatusAnalyzer().analyze(_data_normal())
    assert status["level"] == "normal"
    assert status["recommendation"] == "stay_current"


def test_status_analyzer_moderate_recommends_no_tls():
    status = StatusAnalyzer().analyze(_data_moderate())
    assert status["recommendation"] == "switch_to_no_tls"


def test_auto_adapt_switch_to_no_tls(tmp_path):
    fb = FallbackManager(_make_manager())
    collector = MagicMock()
    collector.collect_all.return_value = _data_moderate()
    adapt = AutoAdapt(fb, collector=collector, log_path=str(tmp_path))
    status = adapt.run_once()
    assert status["recommendation"] == "switch_to_no_tls"
    assert fb.current_protocol == "websocket_plain"


def test_auto_adapt_dns_tunnel(tmp_path):
    fb = FallbackManager(_make_manager())
    collector = MagicMock()
    collector.collect_all.return_value = _data_severe()
    adapt = AutoAdapt(fb, collector=collector, log_path=str(tmp_path))
    adapt.run_once()
    assert fb.current_channel == "doh_tunnel"


def test_auto_adapt_emergency_mode(tmp_path):
    fb = FallbackManager(_make_manager())
    collector = MagicMock()
    collector.collect_all.return_value = _data_critical()
    adapt = AutoAdapt(fb, collector=collector, log_path=str(tmp_path))
    adapt.run_once()
    assert fb.emergency_mode_active is True


def test_auto_adapt_logs_jsonl(tmp_path):
    fb = FallbackManager(_make_manager())
    collector = MagicMock()
    collector.collect_all.return_value = _data_normal()
    adapt = AutoAdapt(fb, collector=collector, log_path=str(tmp_path))
    adapt.run_once()
    log_file = tmp_path / "logs" / "auto_adapt.jsonl"
    assert log_file.is_file()
    line = json.loads(log_file.read_text().strip().splitlines()[-1])
    assert line["recommendation"] == "stay_current"


def test_fallback_enable_obfuscation():
    fb = FallbackManager(_make_manager())
    fb.enable_obfuscation()
    assert fb.current_protocol == "openvpn_obfs4"
    assert fb.obfuscation_enabled is True
