"""Unit tests for Hard Mode modules."""

from hard_mode import HardMode, NetworkConditions
from hard_mode.emergency_fallback import EmergencyFallback
from hard_mode.llm_defender import LLMDefender
from hard_mode.personal_server_manager import PersonalServer, PersonalServerManager
from obfuscation.content_simulator import ContentSimulator
from offline.mesh_connector import MeshP2P
from protocols.icmp_tunnel import ICMPTunnel
from protocols.ssh_tunnel import SSHTunnel


def test_ssh_tunnel_config_without_paramiko():
    t = SSHTunnel("1.2.3.4", "root", password="x")
    cfg = t.generate_config(local_port=10809)
    assert cfg["protocol"] == "ssh_tunnel"
    assert cfg["socks"]["port"] == 10809
    assert cfg["auth"] == "password"


def test_ssh_tunnel_connect_is_safe_without_paramiko():
    t = SSHTunnel("203.0.113.5", "root", password="x")
    if not SSHTunnel.available():
        assert t.connect() is False
        assert t.last_error == "paramiko not installed"


def test_icmp_packet_framing_and_checksum():
    t = ICMPTunnel("203.0.113.9")
    pkt = t.build_packet(b"hello")
    assert pkt[0] == 8  # ICMP echo request type
    assert len(pkt) == 8 + len(b"hello")
    cfg = t.generate_config()
    assert cfg["protocol"] == "icmp_tunnel"


def test_icmp_rejects_oversized_payload():
    t = ICMPTunnel("203.0.113.9")
    try:
        t.build_packet(b"x" * 2000)
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_content_simulator_patterns_deterministic():
    sim = ContentSimulator(seed=42)
    flow = sim.generate_flow(5)
    assert len(flow) == 5
    assert all(isinstance(p, bytes) and p for p in flow)
    assert sim.change_pattern("netflix") is True
    assert sim.change_pattern("unknown") is False


def test_llm_defender_scoring_and_defend():
    d = LLMDefender()
    assert d.score_realness({"size": 800, "interval": 2}) == 0.9
    assert d.score_realness({"size": 5, "interval": 0}) == 0.2
    assert d.analyze_and_adapt({"size": 5, "interval": 0}) == "switched to youtube pattern"
    assert d.current_mode == "youtube"
    assert len(d.defend(b"x" * 5)) == 100
    assert len(d.defend(b"x" * 5000)) == 1400


def test_mesh_p2p_message_handling():
    mesh = MeshP2P(local_port=9099)
    mesh.set_config_provider(lambda: {"proto": "wireguard"})
    assert mesh.handle_message("10.0.0.2", mesh.build_message("ping"))["type"] == "pong"
    resp = mesh.handle_message("10.0.0.2", mesh.build_message("config_request"))
    assert resp["data"]["proto"] == "wireguard"
    mesh.handle_message("10.0.0.3", mesh.build_message("config", {"proto": "xray"}))
    assert mesh.received and mesh.received[0]["config"]["proto"] == "xray"
    assert mesh.handle_message("10.0.0.4", b"not-json")["type"] == "error"


def test_mesh_p2p_discovery():
    mesh = MeshP2P()
    peers = mesh.discover_peers(["192.168.1.10", "192.168.1.11", "192.168.1.10"])
    assert peers == ["192.168.1.10", "192.168.1.11"]


def test_personal_server_manager_roundtrip(tmp_path):
    store = tmp_path / "servers.json"
    mgr = PersonalServerManager(str(store))
    mgr.add(PersonalServer(name="home", ip="198.51.100.7", trusted=True))
    mgr.add(PersonalServer(name="friend", ip="198.51.100.8", trusted=False))
    mgr.save()

    reloaded = PersonalServerManager(str(store))
    reloaded.load()
    assert len(reloaded.list()) == 2
    assert reloaded.best().name == "home"


def test_emergency_fallback_decision_ladder():
    fb = EmergencyFallback()
    assert fb.plan(NetworkConditions(internet_down=True))["selected"] == "mesh_p2p"
    assert fb.plan(NetworkConditions(all_protocols_blocked=True))["selected"] == "doh_tunnel"
    assert fb.plan(NetworkConditions(tcp_blocked=True))["selected"] == "icmp_tunnel"
    assert fb.plan(
        NetworkConditions(dpi_blocking=True, llm_classification=True)
    )["selected"] == "ssh_tunnel"
    assert fb.plan(NetworkConditions(dpi_blocking=True))["selected"] == "content_simulation"
    assert fb.plan(NetworkConditions())["selected"] == "standard_protocols"
    assert fb.escalate("ssh_tunnel") == "icmp_tunnel"
    assert fb.escalate("doh_tunnel") == "mesh_p2p"
    assert fb.escalate("mesh_p2p") == "mesh_p2p"


def test_hard_mode_facade_config_and_readiness():
    hm = HardMode()
    readiness = hm.readiness()
    assert set(readiness) >= {"ssh_tunnel", "icmp_tunnel", "mesh_p2p", "content_simulator"}
    cfg = hm.generate_config()
    assert cfg["hard_mode"] is True
    assert "escalation_ladder" in cfg
    plan = hm.emergency_plan(dpi_blocking=True, llm_classification=True)
    assert plan["selected"] == "ssh_tunnel"
