"""Decide the last-resort channel based on observed network conditions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


@dataclass
class NetworkConditions:
    dpi_blocking: bool = False
    llm_classification: bool = False
    tcp_blocked: bool = False
    internet_down: bool = False


class EmergencyFallback:
    """Ordered escalation: standard protocols -> obfuscation -> SSH -> ICMP -> mesh."""

    LADDER = [
        "standard_protocols",
        "content_simulation",
        "ssh_tunnel",
        "icmp_tunnel",
        "mesh_p2p",
    ]

    def plan(self, conditions: NetworkConditions) -> Dict[str, object]:
        chosen: str
        reason: str

        if conditions.internet_down:
            chosen, reason = "mesh_p2p", "no internet; exchange configs over LAN"
        elif conditions.tcp_blocked:
            chosen, reason = "icmp_tunnel", "TCP blocked; fall back to ICMP"
        elif conditions.dpi_blocking and conditions.llm_classification:
            chosen, reason = "ssh_tunnel", "DPI+LLM blocking; use SSH SOCKS as last resort"
        elif conditions.dpi_blocking or conditions.llm_classification:
            chosen, reason = "content_simulation", "classifier active; reshape traffic"
        else:
            chosen, reason = "standard_protocols", "conditions normal"

        return {
            "selected": chosen,
            "reason": reason,
            "escalation_index": self.LADDER.index(chosen),
            "remaining": self.LADDER[self.LADDER.index(chosen) + 1:],
        }

    def escalate(self, current: str) -> str:
        """Return the next tier below `current`, or the last tier if at the bottom."""
        if current not in self.LADDER:
            return self.LADDER[0]
        idx = self.LADDER.index(current)
        return self.LADDER[min(idx + 1, len(self.LADDER) - 1)]

    def ladder(self) -> List[str]:
        return list(self.LADDER)
