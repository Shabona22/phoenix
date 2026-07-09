"""JA3/JA4 TLS fingerprint simulation for DBF analysis."""

from __future__ import annotations

import hashlib
from typing import Dict, List


class FingerprintSimulator:
    PROFILES = {
        "chrome": "771,4865-4866-4867-49195-49199-52393-52392-49196-49200",
        "firefox": "771,4865-4867-4866-49195-49199-52393-52392-49196-49200",
        "safari": "771,4865-4866-4867-49196-49195-52393-49200-49199-52392",
        "random_bot": "771,255",
    }

    BLOCKED_PROFILES = {"random_bot"}

    def ja3_hash(self, profile: str) -> str:
        ja3 = self.PROFILES.get(profile, self.PROFILES["chrome"])
        return hashlib.md5(ja3.encode()).hexdigest()

    def simulate(self, profile: str = "chrome") -> Dict[str, object]:
        blocked = profile in self.BLOCKED_PROFILES
        return {
            "profile": profile,
            "ja3": self.PROFILES.get(profile, ""),
            "ja3_hash": self.ja3_hash(profile),
            "blocked": blocked,
            "recommendation": "use_no_tls" if blocked else "tls_ok",
        }

    def rank_profiles(self, profiles: List[str] | None = None) -> List[Dict[str, object]]:
        selected = profiles or list(self.PROFILES.keys())
        results = [self.simulate(name) for name in selected]
        return sorted(results, key=lambda item: (item["blocked"], item["profile"]))
