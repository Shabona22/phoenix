"""Collect field measurements for Research Agent analysis."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


class FieldDataCollector:
    def __init__(self, output_dir: str | None = None) -> None:
        base = Path(output_dir or os.getenv("PHOENIX_OUTPUT_DIR", "phoenix-output"))
        self.reports_file = base / "field_reports.json"
        self.reports_file.parent.mkdir(parents=True, exist_ok=True)

    def record(
        self,
        protocol: str,
        latency_ms: float,
        success: bool,
        region: str = "IR",
        notes: str = "",
    ) -> Dict[str, Any]:
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "protocol": protocol,
            "latency_ms": latency_ms,
            "success": success,
            "region": region,
            "notes": notes,
        }
        reports = self.load()
        reports.append(entry)
        self.reports_file.write_text(json.dumps(reports, indent=2), encoding="utf-8")
        return entry

    def load(self) -> List[Dict[str, Any]]:
        if not self.reports_file.is_file():
            return []
        try:
            data = json.loads(self.reports_file.read_text(encoding="utf-8"))
            return data if isinstance(data, list) else []
        except (OSError, ValueError):
            return []

    def summarize(self) -> Dict[str, Any]:
        reports = self.load()
        if not reports:
            return {"count": 0, "protocols": {}}
        by_protocol: Dict[str, List[Dict[str, Any]]] = {}
        for report in reports:
            by_protocol.setdefault(str(report.get("protocol", "unknown")), []).append(report)

        summary: Dict[str, Any] = {"count": len(reports), "protocols": {}}
        for proto, items in by_protocol.items():
            success = sum(1 for item in items if item.get("success"))
            latencies = [float(item["latency_ms"]) for item in items if "latency_ms" in item]
            summary["protocols"][proto] = {
                "samples": len(items),
                "success_rate": round(success / len(items), 3),
                "avg_latency_ms": round(sum(latencies) / len(latencies), 1) if latencies else 0,
            }
        return summary
