"""Resist ML/LLM-based traffic classification by scoring and reshaping flows."""

from __future__ import annotations

from typing import Dict

from obfuscation.content_simulator import ContentSimulator

MIN_NATURAL_SIZE = 100
MAX_NATURAL_SIZE = 1500


class LLMDefender:
    def __init__(self, simulator: ContentSimulator | None = None):
        self.content_simulator = simulator or ContentSimulator()
        self.current_mode = "normal"

    def score_realness(self, traffic_pattern: Dict[str, float]) -> float:
        """Rate how natural a flow looks, 0.0 (synthetic) .. 1.0 (organic)."""
        size = traffic_pattern.get("size", 0)
        interval = traffic_pattern.get("interval", 0)
        if 200 < size < MAX_NATURAL_SIZE and 0.5 < interval < 10:
            return 0.9
        if MIN_NATURAL_SIZE < size < 2000:
            return 0.6
        return 0.2

    def analyze_and_adapt(self, traffic_pattern: Dict[str, float]) -> str:
        """If a flow scores as suspicious, switch to a realistic decoy pattern."""
        if self.score_realness(traffic_pattern) < 0.5:
            self.content_simulator.change_pattern("youtube")
            self.current_mode = "youtube"
            return "switched to youtube pattern"
        self.current_mode = "normal"
        return "pattern is normal"

    def defend(self, traffic: bytes) -> bytes:
        """Normalize an outlier packet into the natural size band."""
        if len(traffic) > MAX_NATURAL_SIZE:
            return traffic[: MAX_NATURAL_SIZE - 100]
        if len(traffic) < MIN_NATURAL_SIZE:
            pad = MIN_NATURAL_SIZE - len(traffic)
            return traffic + (b"\x00" * pad)
        return traffic

    def generate_config(self) -> Dict[str, object]:
        return {
            "enabled": True,
            "current_mode": self.current_mode,
            "natural_size_band": [MIN_NATURAL_SIZE, MAX_NATURAL_SIZE],
            "simulator": self.content_simulator.generate_config(),
        }
