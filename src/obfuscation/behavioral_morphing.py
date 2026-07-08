"""Behavioral traffic morphing configuration."""

from __future__ import annotations

import random
from typing import List


class BehavioralMorphing:
    PROFILES = ["browsing", "streaming", "messaging", "gaming"]

    def __init__(self):
        self._current = "browsing"

    def morph(self) -> str:
        self._current = random.choice(self.PROFILES)
        return self._current

    def generate_config(self) -> dict:
        return {
            "enabled": True,
            "current_profile": self._current,
            "profiles": self._profile_params(self._current),
        }

    def _profile_params(self, profile: str) -> dict:
        params = {
            "browsing": {"burst_size": 4, "idle_range": [2, 8]},
            "streaming": {"burst_size": 16, "idle_range": [0, 2]},
            "messaging": {"burst_size": 2, "idle_range": [5, 30]},
            "gaming": {"burst_size": 8, "idle_range": [0, 1]},
        }
        return params.get(profile, params["browsing"])
