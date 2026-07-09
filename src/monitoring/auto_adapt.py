"""Automatic monitoring and protocol adaptation loop."""

from __future__ import annotations

import json
import os
import threading
import time
from pathlib import Path
from typing import Any, Callable, Dict, Optional

from healer.fallback_manager import FallbackManager
from monitoring.data_collector import DataCollector
from monitoring.status_analyzer import StatusAnalyzer
from offline.alternative_channel import AlternativeChannel


class AutoAdapt:
    def __init__(
        self,
        fallback_manager: FallbackManager,
        collector: Optional[DataCollector] = None,
        analyzer: Optional[StatusAnalyzer] = None,
        alternative_channel: Optional[AlternativeChannel] = None,
        interval: int = 60,
        log_path: Optional[str] = None,
        on_status: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> None:
        self.fallback = fallback_manager
        self.collector = collector or DataCollector()
        self.analyzer = analyzer or StatusAnalyzer()
        self.alt_channel = alternative_channel or AlternativeChannel()
        self.interval = interval
        self.on_status = on_status
        base = Path(log_path or os.getenv("PHOENIX_OUTPUT_DIR", "phoenix-output"))
        self.log_path = base / "logs" / "auto_adapt.jsonl"
        self.is_running = False
        self._thread: Optional[threading.Thread] = None
        self.last_status: Dict[str, Any] = {}

    def start(self) -> None:
        if self.is_running:
            return
        self.is_running = True
        self._thread = threading.Thread(target=self._adapt_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self.is_running = False

    def run_once(self) -> Dict[str, Any]:
        data = self.collector.collect_all()
        status = self.analyzer.analyze(data)
        self._apply_changes(status)
        self._log_status(status, data)
        self.last_status = status
        if self.on_status:
            self.on_status(status)
        return status

    def _adapt_loop(self) -> None:
        while self.is_running:
            self.run_once()
            time.sleep(self.interval)

    def _apply_changes(self, status: Dict[str, Any]) -> None:
        recommendation = status.get("recommendation", "stay_current")
        if recommendation == "switch_to_no_tls":
            self.fallback.switch_to_no_tls()
        elif recommendation == "switch_to_dns_tunnel":
            self.fallback.switch_to_dns_tunnel()
        elif recommendation == "enable_mesh_and_qr":
            self.fallback.enable_emergency_mode()
            node = self.fallback.get_active_node()
            if node:
                self.alt_channel.send_config(
                    node.node_id,
                    {"protocol": self.fallback.current_protocol, "server": {"ip": node.ip}},
                )
        elif recommendation == "enable_obfuscation":
            self.fallback.enable_obfuscation()

    def _log_status(self, status: Dict[str, Any], data: Dict[str, Any]) -> None:
        entry = {
            "timestamp": data.get("timestamp", time.time()),
            "level": status.get("level"),
            "type": status.get("type"),
            "latency": status.get("latency"),
            "loss": status.get("loss"),
            "trend": status.get("trend"),
            "recommendation": status.get("recommendation"),
            "protocol": self.fallback.current_protocol,
            "channel": self.fallback.current_channel,
        }
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        with self.log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry) + "\n")
