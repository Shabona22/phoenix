"""Unit tests for Phoenix V10 outage fixes."""

from healer.auto_healer_enhanced import AutoHealerEnhanced
from healer.fallback_manager import FallbackManager
from monitoring.user_report_collector import UserReportCollector
from offline.alternative_channel import AlternativeChannel
from offline.emergency_paper_config import EmergencyPaperConfig
from orchestrator.personal_server_manager import OrchestratorPersonalServerManager
from protocols.doh_tunnel import DoHTunnel


class _StubNodeManager:
    def switch_node(self):
        return None


def test_alternative_channel_mesh_success(tmp_path):
    alt = AlternativeChannel(output_dir=str(tmp_path))
    ok = alt.send_config("u1", {"protocol": "wireguard", "server": {"ip": "10.0.0.1"}})
    assert ok is True
    assert alt.last_channel == "mesh"


def test_alternative_channel_usb_fallback(tmp_path):
    alt = AlternativeChannel(output_dir=str(tmp_path))
    alt.fallback_order = ["usb"]
    ok = alt.send_config("u2", {"protocol": "openvpn"})
    assert ok and alt.last_channel == "usb"
    assert (tmp_path / "offline_exports" / "config_u2.txt").exists()


def test_auto_healer_enhanced_recovery():
    fb = FallbackManager(_StubNodeManager())
    healer = AutoHealerEnhanced(fb)
    healer.set_connected_check(lambda: False)
    assert healer.attempt_recovery() is True
    assert healer.recovery_history[-1]["mode"] == "protocol"


def test_auto_healer_channel_and_emergency():
    fb = FallbackManager(_StubNodeManager())
    for _ in range(len(fb.PROTOCOL_CHAIN) - 1):
        fb.switch_protocol()
    fb.switch_node()
    healer = AutoHealerEnhanced(fb)
    healer.set_connected_check(lambda: False)
    healer.attempt_recovery()
    modes = [h["mode"] for h in healer.recovery_history]
    assert "channel" in modes or "emergency" in modes


def test_doh_tunnel_chunk_and_transport():
    t = DoHTunnel(tunnel_id="abc123")
    sent = []
    ok = t.send_data(b"hello-world", transport=lambda chunk, q: sent.append(q) or True)
    assert ok and len(sent) == 1
    assert "abc123" in sent[0]
    cfg = t.generate_config()
    assert cfg["protocol"] == "doh_tunnel"


def test_orchestrator_personal_server_manager(tmp_path):
    store = tmp_path / "personal_servers.json"
    mgr = OrchestratorPersonalServerManager(str(store))
    assert mgr.add_server("home", "198.51.100.7", location="TR", fixed_ip=True)
    assert len(mgr.get_active_servers()) == 1
    assert mgr.deploy_to_personal_server("home", {"protocol": "xray"})
    assert (tmp_path / "personal_deploy" / "home_config.json").exists()


def test_emergency_paper_config(tmp_path):
    paper = EmergencyPaperConfig(output_dir=str(tmp_path))
    paths = paper.generate_bundle("u99", [{"protocol": "openvpn", "server": {"ip": "1.2.3.4", "port": 1194}}])
    assert paths["card"].endswith(".png")
    assert (tmp_path / "paper_configs" / "config_text_u99.txt").exists()


def test_user_report_collector(tmp_path):
    store = tmp_path / "reports.json"
    c = UserReportCollector(store_path=str(store))
    c.collect_report({"status": "connected", "protocol": "xray", "latency_ms": 100})
    c.collect_report({"status": "failed", "protocol": "openvpn"})
    stats = c.get_stats()
    assert stats["total"] == 2
    assert stats["success_rate"] == 50.0
