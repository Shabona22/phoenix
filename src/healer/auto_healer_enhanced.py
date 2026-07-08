"""Enhanced auto-healing for long outages (24h+)."""

from __future__ import annotations

import threading
import time
from datetime import datetime, timezone
from typing import Callable, Dict, List, Optional

from healer.fallback_manager import FallbackManager
from verification.user_traffic_validator import TrafficValidator


class AutoHealerEnhanced:
    """Poll connectivity and escalate through protocol, node, channel, emergency."""

    RECOVERY_MODES = ["protocol", "node", "channel", "emergency"]

    def __init__(
        self,
        fallback_manager: FallbackManager,
        traffic_validator: Optional[TrafficValidator] = None,
        check_interval: int = 30,
        on_alert: Optional[Callable[[str], None]] = None,
    ):
        self.fallback = fallback_manager
        self.traffic_validator = traffic_validator
        self.check_interval = check_interval
        self.on_alert = on_alert or (lambda msg: None)
        self.recovery_history: List[Dict[str, str]] = []
        self.is_healing = False
        self._thread: Optional[threading.Thread] = None
        self._connected_check: Callable[[], bool] = self._default_connected_check

    def set_connected_check(self, checker: Callable[[], bool]) -> None:
        self._connected_check = checker

    def _default_connected_check(self) -> bool:
        if self.traffic_validator:
            return self.traffic_validator.is_connected()
        return True

    def start_healing(self) -> None:
        if self.is_healing:
            return
        self.is_healing = True
        self._thread = threading.Thread(target=self._heal_loop, daemon=True)
        self._thread.start()

    def stop_healing(self) -> None:
        self.is_healing = False

    def _heal_loop(self) -> None:
        while self.is_healing:
            if not self._connected_check():
                self.attempt_recovery()
            time.sleep(self.check_interval)

    def attempt_recovery(self) -> bool:
        for mode in self.RECOVERY_MODES:
            if self._try_recovery_mode(mode):
                entry = {
                    "mode": mode,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
                self.recovery_history.append(entry)
                return True
        self.on_alert("Connection lost; all recovery modes failed")
        return False

    def _try_recovery_mode(self, mode: str) -> bool:
        try:
            if mode == "protocol":
                return self.fallback.switch_protocol()
            if mode == "node":
                return self.fallback.switch_node()
            if mode == "channel":
                return self.fallback.switch_channel()
            if mode == "emergency":
                self.fallback.emergency_mode()
                return True
        except (OSError, RuntimeError):
            return False
        return False

    def generate_config(self) -> Dict[str, object]:
        return {
            "enabled": self.is_healing,
            "check_interval_seconds": self.check_interval,
            "recovery_modes": self.RECOVERY_MODES,
            "history_count": len(self.recovery_history),
        }
