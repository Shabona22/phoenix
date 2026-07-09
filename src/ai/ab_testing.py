"""Simple A/B assignment for protocol or obfuscation variants."""

from __future__ import annotations

import hashlib
from typing import Dict, List


class ABTesting:
    def __init__(self, variants: List[str]):
        if len(variants) < 2:
            raise ValueError("need at least two variants")
        self.variants = variants

    def assign(self, user_id: str) -> str:
        digest = hashlib.sha256(user_id.encode()).hexdigest()
        idx = int(digest[:8], 16) % len(self.variants)
        return self.variants[idx]

    def report(self, assignments: Dict[str, str]) -> Dict[str, object]:
        counts = {v: 0 for v in self.variants}
        for variant in assignments.values():
            if variant in counts:
                counts[variant] += 1
        total = sum(counts.values()) or 1
        return {
            "variants": self.variants,
            "distribution": {k: round(v / total, 3) for k, v in counts.items()},
        }
