"""TLS fingerprint rotation config."""

from __future__ import annotations

import random
from typing import Dict, List


class TLSFingerprint:
    PROFILES = [
        {"name": "chrome_120", "ja3": "771,4865-4866-4867-49195-49199-49196-49200-52393-52392-49171-49172-156-157-47-53-49160-49170-10"},
        {"name": "firefox_121", "ja3": "771,4865-4867-4866-49195-49199-52393-52392-49196-49200-49162-49161-49171-49172-51-57-47-53-10"},
        {"name": "safari_17", "ja3": "771,4865-4866-4867-49196-49195-52393-49200-49162-49161-49172-49171-157-156-53-47-49160-49170-10"},
    ]

    def __init__(self):
        self._current_index = 0

    def list_profiles(self) -> List[Dict[str, str]]:
        return self.PROFILES

    def current_profile(self) -> Dict[str, str]:
        return self.PROFILES[self._current_index]

    def rotate(self) -> Dict[str, str]:
        self._current_index = (self._current_index + 1) % len(self.PROFILES)
        return self.current_profile()

    def random_profile(self) -> Dict[str, str]:
        return random.choice(self.PROFILES)

    def generate_config(self) -> Dict[str, object]:
        profile = self.current_profile()
        return {
            "tls_fingerprint": profile["ja3"],
            "profile_name": profile["name"],
            "uTLS_enabled": True,
            "rotate_on_fallback": True,
        }
