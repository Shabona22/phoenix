"""Time synchronization keeper."""

from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Dict


class TimeKeeper:
    MAX_DRIFT_SECONDS = 30

    def __init__(self):
        self._reference: float = time.time()

    def now_utc(self) -> datetime:
        return datetime.now(timezone.utc)

    def check_drift(self) -> Dict[str, object]:
        drift = abs(time.time() - self._reference)
        return {
            "drift_seconds": drift,
            "acceptable": drift <= self.MAX_DRIFT_SECONDS,
            "utc_now": self.now_utc().isoformat(),
        }

    def sync_reference(self) -> None:
        self._reference = time.time()
