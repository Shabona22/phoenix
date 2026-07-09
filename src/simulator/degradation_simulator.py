"""Degradation-Based Filtering (DBF) connection simulator."""

from __future__ import annotations

import random
import time
from typing import Any, Dict, Optional, Tuple


class _MockConnection:
    """Minimal connection object for RST simulation."""

    def __init__(self) -> None:
        self.closed = False

    def close(self) -> None:
        self.closed = True


class DegradationSimulator:
    """
    Simulate DBF behaviour:
    - delay injection
    - packet loss
    - jitter
    - random RST after sustained degradation
    """

    def __init__(self, seed: Optional[int] = None) -> None:
        if seed is not None:
            random.seed(seed)
        self.modes = {
            "delay": self._inject_delay,
            "loss": self._inject_loss,
            "jitter": self._inject_jitter,
            "rst": self._inject_rst,
        }
        self.active = True
        self.thresholds: Dict[str, Tuple[int, ...] | Tuple[float, ...]] = {
            "delay_ms": (50, 500),
            "loss_percent": (1, 5),
            "jitter_ms": (10, 100),
            "timeout_seconds": (600,),
        }

    def degrade_connection(self, connection: Optional[object] = None) -> Dict[str, Any]:
        conn = connection or _MockConnection()
        delay = random.randint(*self.thresholds["delay_ms"])  # type: ignore[arg-type]
        loss = random.uniform(*self.thresholds["loss_percent"])  # type: ignore[arg-type]
        jitter = random.randint(*self.thresholds["jitter_ms"])  # type: ignore[arg-type]

        results: Dict[str, Any] = {
            "delay": self._inject_delay(conn, delay),
            "loss": self._inject_loss(conn, loss),
            "jitter": self._inject_jitter(conn, jitter),
        }
        if random.random() < 0.01:
            results["rst"] = self._inject_rst(conn)
        return results

    def _inject_delay(self, conn: object, ms: int) -> bool:
        del conn
        time.sleep(ms / 1000)
        return True

    def _inject_loss(self, conn: object, percent: float) -> bool:
        del conn
        return random.random() < percent / 100

    def _inject_jitter(self, conn: object, ms: int) -> bool:
        del conn
        jitter_delay = random.randint(0, ms)
        time.sleep(jitter_delay / 1000)
        return True

    def _inject_rst(self, conn: object) -> bool:
        try:
            close = getattr(conn, "close", None)
            if callable(close):
                close()
            return True
        except OSError:
            return False

    def simulate_session(self, duration_seconds: int = 2) -> Dict[str, Any]:
        """Simulate a session; default duration kept short for tests."""
        start_time = time.time()
        results: Dict[str, Any] = {
            "total_requests": 0,
            "degraded_requests": 0,
            "rst_count": 0,
            "survived": True,
        }

        while time.time() - start_time < duration_seconds:
            results["total_requests"] += 1
            if random.random() < 0.3:
                results["degraded_requests"] += 1
                if random.random() < 0.05:
                    results["rst_count"] += 1
            time.sleep(0.01)

        if results["rst_count"] > 3:
            results["survived"] = False
        return results
