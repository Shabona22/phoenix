"""Collect anonymized field reports from users."""

from __future__ import annotations

import hashlib
import json
import os
import secrets
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Dict, List, Optional


class UserReportCollector:
    def __init__(
        self,
        report_url: str = "",
        store_path: Optional[str] = None,
        collect_interval: int = 3600,
        sample_fn: Optional[Callable[[], Dict[str, object]]] = None,
    ):
        base = Path(store_path or os.getenv("PHOENIX_OUTPUT_DIR", "phoenix-output"))
        self.store_path = base / "user_reports.json"
        self.report_url = report_url
        self.collect_interval = collect_interval
        self.sample_fn = sample_fn or self._default_sample
        self.reports: List[Dict[str, object]] = []
        self.is_collecting = False
        self._thread: Optional[threading.Thread] = None
        self._load()

    def _load(self) -> None:
        if not self.store_path.exists():
            return
        try:
            self.reports = json.loads(self.store_path.read_text())
        except (ValueError, OSError):
            self.reports = []

    def _save(self) -> None:
        self.store_path.parent.mkdir(parents=True, exist_ok=True)
        self.store_path.write_text(json.dumps(self.reports[-500:], indent=2))

    @staticmethod
    def _anonymous_id(seed: str) -> str:
        return hashlib.sha256(seed.encode()).hexdigest()[:16]

    def _default_sample(self) -> Dict[str, object]:
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "user_hash": self._anonymous_id(secrets.token_hex(8)),
            "status": "unknown",
            "protocol": "xray",
            "latency_ms": None,
        }

    def collect_report(self, report: Optional[Dict[str, object]] = None) -> Dict[str, object]:
        entry = report or self.sample_fn()
        self.reports.append(entry)
        self._save()
        return entry

    def start_collecting(self) -> None:
        if self.is_collecting:
            return
        self.is_collecting = True
        self._thread = threading.Thread(target=self._collect_loop, daemon=True)
        self._thread.start()

    def stop_collecting(self) -> None:
        self.is_collecting = False

    def _collect_loop(self) -> None:
        while self.is_collecting:
            self.collect_report()
            time.sleep(self.collect_interval)

    def get_reports(self, last_n: int = 10) -> List[Dict[str, object]]:
        return self.reports[-last_n:]

    def get_stats(self) -> Dict[str, object]:
        if not self.reports:
            return {"total": 0, "success_rate": 0.0}
        success = sum(1 for r in self.reports if r.get("status") == "connected")
        return {
            "total": len(self.reports),
            "success_rate": round(success / len(self.reports) * 100, 1),
        }

    def generate_config(self) -> Dict[str, object]:
        return {
            "enabled": self.is_collecting,
            "store_path": str(self.store_path),
            "stats": self.get_stats(),
        }
