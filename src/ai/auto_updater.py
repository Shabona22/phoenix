"""Suggest config updates when filtering is detected."""

from __future__ import annotations

from typing import Any, Dict

from ai.dynamic_config_generator import DynamicConfigGenerator
from ai.feedback_loop import FeedbackLoop


class AutoUpdater:
    def __init__(self):
        self.feedback = FeedbackLoop()
        self.generator = DynamicConfigGenerator()

    def propose_update(self, base_config: Dict[str, Any]) -> Dict[str, object]:
        summary = self.feedback.summarize()
        severity = summary.get("analysis", {}).get("severity", "none")
        threat = "high" if severity == "high" else "medium" if severity == "medium" else "low"
        updated = self.generator.adapt(base_config, threat_level=threat)
        return {
            "threat_level": threat,
            "summary": summary,
            "config": updated,
            "auto_apply": threat == "high",
        }
