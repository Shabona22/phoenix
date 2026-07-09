"""Unit tests for DBF simulator modules."""

from simulator.degradation_simulator import DegradationSimulator
from simulator.iran_filter_simulator import IranFilterSimulator


def test_degradation_simulator_session():
    sim = DegradationSimulator(seed=1)
    result = sim.simulate_session(duration_seconds=1)
    assert result["total_requests"] > 0
    assert "survived" in result


def test_degradation_connection_injection():
    sim = DegradationSimulator(seed=2)
    result = sim.degrade_connection()
    assert "delay" in result
    assert "loss" in result
    assert "jitter" in result


def test_iran_filter_prefers_no_tls():
    sim = IranFilterSimulator(profile="tls_fingerprint", seed=3)
    tls_cfg = {"protocol": "xray", "tls": True}
    no_tls_cfg = {"protocol": "websocket_plain", "tls": False}
    tls_result = sim.test_config(tls_cfg)
    no_tls_result = sim.test_config(no_tls_cfg)
    assert no_tls_result["stability_score"] >= tls_result["stability_score"]


def test_iran_filter_rank_protocols():
    sim = IranFilterSimulator(seed=4)
    configs = [
        {"protocol": "xray", "tls": True},
        {"protocol": "tcp_plain", "tls": False},
        {"protocol": "websocket_plain", "tls": False},
    ]
    ranked = sim.rank_protocols(configs)
    assert ranked[0]["protocol"] in ("websocket_plain", "tcp_plain")
