"""Test generated configs against DBF degradation simulator."""

from __future__ import annotations

from typing import Any, Dict, List

from simulator.iran_filter_simulator import IranFilterSimulator


class ConfigTester:
    def __init__(self, profile: str = "dbf") -> None:
        self.simulator = IranFilterSimulator(profile=profile)

    def test_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        return self.simulator.test_config(config)

    def test_many(self, configs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return self.simulator.rank_protocols(configs)

    def best_protocol(self, configs: List[Dict[str, Any]]) -> str:
        ranked = self.test_many(configs)
        if not ranked:
            return "websocket_plain"
        return str(ranked[0]["protocol"])
