"""Unit tests for Research Agent and config tester."""

from ai.fingerprint_simulator import FingerprintSimulator
from research.field_data_collector import FieldDataCollector
from research.research_agent import ResearchAgent
from utils.config_tester import ConfigTester


def test_research_agent_offline_analysis():
    agent = ResearchAgent(sources={}, timeout=1)
    data = agent.collect_data()
    analysis = agent.analyze_findings(data)
    assert "recommendations" in analysis
    assert len(analysis["recommendations"]) >= 1


def test_research_agent_report():
    agent = ResearchAgent(sources={})
    report = agent.generate_report()
    assert "Research Agent Report" in report


def test_field_data_collector(tmp_path):
    collector = FieldDataCollector(output_dir=str(tmp_path))
    collector.record("websocket_plain", 120.0, True)
    summary = collector.summarize()
    assert summary["count"] == 1
    assert "websocket_plain" in summary["protocols"]


def test_config_tester_prefers_no_tls():
    tester = ConfigTester(profile="tls_fingerprint")
    configs = [
        {"protocol": "xray", "tls": True},
        {"protocol": "websocket_plain", "tls": False},
    ]
    best = tester.best_protocol(configs)
    assert best == "websocket_plain"


def test_fingerprint_simulator_blocks_bot_profile():
    sim = FingerprintSimulator()
    result = sim.simulate("random_bot")
    assert result["blocked"] is True
    assert result["recommendation"] == "use_no_tls"
