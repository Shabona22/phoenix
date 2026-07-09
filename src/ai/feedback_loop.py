"""Close the loop between field reports and config recommendations."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict, List, Optional

from ai.filtering_detector import FilteringDetector


class FeedbackLoop:
    def __init__(self, reports_path: Optional[str] = None):
        base = Path(reports_path or os.getenv("PHOENIX_OUTPUT_DIR", "phoenix-output"))
        self.reports_path = base / "user_reports.json"
        self.detector = FilteringDetector()

    def load_reports(self) -> List[Dict[str, object]]:
        if not self.reports_path.is_file():
            return []
        try:
            data = json.loads(self.reports_path.read_text())
            return data if isinstance(data, list) else []
        except (ValueError, OSError):
            return []

    def summarize(self) -> Dict[str, object]:
        reports = self.load_reports()
        if not reports:
            return {"count": 0, "recommendation": "collect_more_reports"}

        failed = sum(1 for r in reports if r.get("status") != "connected")
        failure_rate = failed / len(reports)
        latencies = [r["latency_ms"] for r in reports if isinstance(r.get("latency_ms"), (int, float))]
        avg_latency = sum(latencies) / len(latencies) if latencies else 0

        analysis = self.detector.analyze(
            {"latency_ms": avg_latency, "failure_rate": failure_rate, "reset_rate": failure_rate * 0.5}
        )
        return {
            "count": len(reports),
            "failure_rate": round(failure_rate, 3),
            "avg_latency_ms": round(avg_latency, 1),
            "analysis": analysis,
            "recommendation": analysis["recommended_action"],
        }
