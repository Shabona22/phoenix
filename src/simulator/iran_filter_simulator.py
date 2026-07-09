"""Iran censorship simulator built on DBF degradation model."""

from __future__ import annotations

from typing import Any, Dict, List

from simulator.degradation_simulator import DegradationSimulator


class IranFilterSimulator:
    """Combine DBF degradation with TLS fingerprint and blocking profiles."""

    PROFILES = {
        "dbf": {"degradation_rate": 0.3, "rst_rate": 0.05, "tls_fingerprint_block": False},
        "tls_fingerprint": {"degradation_rate": 0.2, "rst_rate": 0.1, "tls_fingerprint_block": True},
        "hard_block": {"degradation_rate": 0.5, "rst_rate": 0.2, "tls_fingerprint_block": True},
    }

    def __init__(self, profile: str = "dbf", seed: int | None = 42) -> None:
        if profile not in self.PROFILES:
            raise ValueError(f"Unknown profile: {profile}")
        self.profile_name = profile
        self.profile = self.PROFILES[profile]
        self.degradation = DegradationSimulator(seed=seed)

    def test_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        uses_tls = bool(config.get("tls", True))
        protocol = config.get("protocol", "unknown")
        session = self.degradation.simulate_session(duration_seconds=1)

        blocked_by_tls = self.profile["tls_fingerprint_block"] and uses_tls
        no_tls_bonus = protocol in ("websocket_plain", "tcp_plain", "http_upgrade")

        score = 100
        if blocked_by_tls:
            score -= 40
        if session["rst_count"] > 0:
            score -= 20
        if session["degraded_requests"] > session["total_requests"] * 0.2:
            score -= 15
        if no_tls_bonus:
            score += 10
        score = max(0, min(100, score))

        return {
            "profile": self.profile_name,
            "protocol": protocol,
            "uses_tls": uses_tls,
            "blocked_by_tls_fingerprint": blocked_by_tls,
            "session": session,
            "stability_score": score,
            "passed": score >= 60,
        }

    def rank_protocols(self, configs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        results = [self.test_config(cfg) for cfg in configs]
        return sorted(results, key=lambda item: item["stability_score"], reverse=True)
