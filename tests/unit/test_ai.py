"""Unit tests for AI modules."""

from ai.ab_testing import ABTesting
from ai.auto_updater import AutoUpdater
from ai.dynamic_config_generator import DynamicConfigGenerator
from ai.feedback_loop import FeedbackLoop
from ai.filtering_detector import FilteringDetector


def test_filtering_detector_high_severity():
    detector = FilteringDetector()
    result = detector.analyze({"latency_ms": 1200, "failure_rate": 0.6, "reset_rate": 0.5})
    assert result["filtered"] is True
    assert result["severity"] == "high"
    assert result["recommended_action"] == "switch_protocol_and_enable_obfuscation"


def test_filtering_detector_none():
    detector = FilteringDetector()
    result = detector.analyze({"latency_ms": 50, "failure_rate": 0.0, "reset_rate": 0.0})
    assert result["filtered"] is False
    assert result["severity"] == "none"


def test_dynamic_config_generator_adapts_high_threat():
    gen = DynamicConfigGenerator()
    base = {"server": {"host": "1.2.3.4", "port": 443}}
    adapted = gen.adapt(base, threat_level="high")
    assert adapted["dynamic"] is True
    assert adapted["obfuscation"]["enabled"] is True


def test_ab_testing_assign_and_report():
    ab = ABTesting(["xray", "wireguard"])
    a = ab.assign("user-1")
    b = ab.assign("user-2")
    assert a in ab.variants
    assert b in ab.variants
    report = ab.report({"u1": a, "u2": b, "u3": a})
    assert report["distribution"][a] > 0


def test_feedback_loop_empty():
    loop = FeedbackLoop(reports_path="/tmp/nonexistent_phoenix_reports_dir")
    summary = loop.summarize()
    assert summary["count"] == 0
    assert summary["recommendation"] == "collect_more_reports"


def test_auto_updater_propose():
    updater = AutoUpdater()
    result = updater.propose_update({"server": {"host": "10.0.0.1", "port": 443}})
    assert "config" in result
    assert result["threat_level"] in ("low", "medium", "high")
