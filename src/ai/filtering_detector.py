"""Detect censorship patterns from connection metrics."""

from __future__ import annotations

from typing import Dict, List


class FilteringDetector:
    """Rule-based detector; no external ML models required."""

    THRESHOLDS = {
        "high_latency_ms": 800,
        "failure_rate": 0.4,
        "reset_rate": 0.3,
    }

    def analyze(self, metrics: Dict[str, float]) -> Dict[str, object]:
        latency = metrics.get("latency_ms", 0)
        failure_rate = metrics.get("failure_rate", 0)
        reset_rate = metrics.get("reset_rate", 0)
        signals: List[str] = []

        if latency > self.THRESHOLDS["high_latency_ms"]:
            signals.append("high_latency")
        if failure_rate >= self.THRESHOLDS["failure_rate"]:
            signals.append("connection_failures")
        if reset_rate >= self.THRESHOLDS["reset_rate"]:
            signals.append("tcp_resets")
        if metrics.get("degradation_rate", 0) >= 0.25:
            signals.append("dbf_degradation")
        if metrics.get("jitter_ms", 0) >= 80:
            signals.append("dbf_jitter")

        severity = "none"
        if len(signals) >= 2:
            severity = "high"
        elif signals:
            severity = "medium"

        return {
            "filtered": severity != "none",
            "severity": severity,
            "signals": signals,
            "recommended_action": self._recommend(severity),
        }

    def _recommend(self, severity: str) -> str:
        if severity == "high":
            return "switch_to_no_tls_protocols"
        if severity == "medium":
            return "enable_content_simulation"
        return "continue"
