"""Analyze collected network data and classify disruption."""

from __future__ import annotations

from typing import Any, Dict, List

from ai.filtering_detector import FilteringDetector


class StatusAnalyzer:
    LEVELS = ("normal", "light", "moderate", "severe", "critical")

    def __init__(self) -> None:
        self.detector = FilteringDetector()
        self._history: List[Dict[str, Any]] = []

    def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        avg_latency = self._calculate_avg_latency(data)
        loss_percent = self._calculate_loss_percent(data)
        filtering_type = self._detect_filtering_type(data)
        level = self._determine_severity(avg_latency, loss_percent, filtering_type)
        blocking = level in ("severe", "critical") or filtering_type in ("blocking", "stealth_blocking")

        dbf = self.detector.analyze(
            {
                "latency_ms": float(avg_latency),
                "failure_rate": loss_percent / 100.0,
                "reset_rate": (loss_percent / 100.0) * 0.5,
                "degradation_rate": 0.35 if filtering_type == "degradation" else 0.0,
                "jitter_ms": 90.0 if filtering_type == "degradation" else 0.0,
            }
        )
        if dbf.get("severity") == "high" and level not in ("severe", "critical"):
            if filtering_type in ("blocking", "stealth_blocking"):
                level = "severe"
            elif level == "normal":
                level = "moderate"
            elif level == "light":
                level = "moderate"

        status = {
            "level": level,
            "type": filtering_type,
            "latency": avg_latency,
            "loss": loss_percent,
            "blocking": blocking,
            "trend": "stable",
            "recommendation": self._generate_recommendation(level),
            "dbf_signals": dbf.get("signals", []),
        }
        self._history.append(status)
        if len(self._history) > 3:
            self._history = self._history[-3:]
        status["trend"] = self._compute_trend()
        return status

    def _calculate_avg_latency(self, data: Dict[str, Any]) -> int:
        latencies: List[int] = []
        for test in data.get("http_tests", {}).values():
            if isinstance(test.get("latency"), (int, float)):
                latencies.append(int(test["latency"]))
        if latencies:
            return int(sum(latencies) / len(latencies))
        return 0

    def _calculate_loss_percent(self, data: Dict[str, Any]) -> int:
        loss_count = 0
        total = 0
        for test in data.get("ping_tests", {}).values():
            total += 1
            if not test.get("success", False):
                loss_count += 1
        if total == 0:
            return 0
        return int((loss_count / total) * 100)

    def _detect_filtering_type(self, data: Dict[str, Any]) -> str:
        dns_blocked = any(not t.get("success", False) for t in data.get("dns_tests", {}).values())
        http_blocked = any(not t.get("success", False) for t in data.get("http_tests", {}).values())
        if dns_blocked and http_blocked:
            return "stealth_blocking"
        if http_blocked:
            return "blocking"
        avg_latency = self._calculate_avg_latency(data)
        if avg_latency >= 150:
            return "degradation"
        return "none"

    def _determine_severity(self, latency: int, loss: int, filtering_type: str) -> str:
        if filtering_type == "stealth_blocking":
            return "critical"
        if filtering_type == "blocking":
            if loss >= 10 or latency >= 500:
                return "critical"
            return "severe"
        if latency < 50 and loss < 1:
            return "normal"
        if latency < 150 and loss < 3:
            return "light"
        if latency < 300 and loss < 5:
            return "moderate"
        if latency < 500 and loss < 10:
            return "severe"
        return "critical"

    def _generate_recommendation(self, level: str) -> str:
        mapping = {
            "normal": "stay_current",
            "light": "enable_obfuscation",
            "moderate": "switch_to_no_tls",
            "severe": "switch_to_dns_tunnel",
            "critical": "enable_mesh_and_qr",
        }
        return mapping.get(level, "stay_current")

    def _compute_trend(self) -> str:
        if len(self._history) < 2:
            return "stable"
        levels = [self.LEVELS.index(item["level"]) for item in self._history]
        if levels[-1] > levels[0]:
            return "worsening"
        if levels[-1] < levels[0]:
            return "improving"
        return "stable"
