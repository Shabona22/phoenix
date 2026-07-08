"""Budget and traffic alert manager."""

from __future__ import annotations

from typing import Dict, List, Optional


class BudgetAlert:
    def __init__(self, traffic_limit_gb: float = 1000.0, alert_threshold: float = 0.8):
        self.traffic_limit_gb = traffic_limit_gb
        self.alert_threshold = alert_threshold
        self._alerts: List[str] = []

    def check_traffic(self, used_gb: float, node_name: str = "") -> Dict[str, object]:
        ratio = used_gb / self.traffic_limit_gb if self.traffic_limit_gb else 0
        alert = ratio >= self.alert_threshold
        if alert:
            msg = f"Traffic alert for {node_name or 'node'}: {used_gb:.2f}GB / {self.traffic_limit_gb:.2f}GB"
            self._alerts.append(msg)
        return {
            "used_gb": used_gb,
            "limit_gb": self.traffic_limit_gb,
            "ratio": ratio,
            "alert": alert,
        }

    def get_alerts(self) -> List[str]:
        return list(self._alerts)

    def clear_alerts(self) -> None:
        self._alerts.clear()
