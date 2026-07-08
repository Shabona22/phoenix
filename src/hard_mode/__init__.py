"""Hard Mode facade — last line of defense against advanced censorship.

Aggregates the hard-mode layers behind one object so callers (CLI, healer,
report) can query readiness, build a combined config, and pick an emergency
channel without wiring each module by hand.
"""

from __future__ import annotations

from typing import Dict, Optional

from obfuscation.content_simulator import ContentSimulator
from offline.mesh_connector import MeshP2P
from protocols.icmp_tunnel import ICMPTunnel
from protocols.ssh_tunnel import SSHTunnel

from .emergency_fallback import EmergencyFallback, NetworkConditions
from .llm_defender import LLMDefender
from .personal_server_manager import PersonalServer, PersonalServerManager

__all__ = [
    "HardMode",
    "EmergencyFallback",
    "NetworkConditions",
    "LLMDefender",
    "PersonalServer",
    "PersonalServerManager",
]


class HardMode:
    def __init__(self, personal_store: Optional[str] = None):
        self.simulator = ContentSimulator()
        self.llm_defender = LLMDefender(self.simulator)
        self.mesh = MeshP2P()
        self.fallback = EmergencyFallback()
        self.personal_servers = PersonalServerManager(personal_store)
        self.personal_servers.load()

    def readiness(self) -> Dict[str, bool]:
        return {
            "ssh_tunnel": SSHTunnel.available(),
            "icmp_tunnel": ICMPTunnel.available(),
            "content_simulator": True,
            "llm_defender": True,
            "mesh_p2p": True,
            "personal_servers": bool(self.personal_servers.servers),
        }

    def emergency_plan(
        self,
        dpi_blocking: bool = False,
        llm_classification: bool = False,
        tcp_blocked: bool = False,
        internet_down: bool = False,
    ) -> Dict[str, object]:
        conditions = NetworkConditions(
            dpi_blocking=dpi_blocking,
            llm_classification=llm_classification,
            tcp_blocked=tcp_blocked,
            internet_down=internet_down,
        )
        return self.fallback.plan(conditions)

    def generate_config(self) -> Dict[str, object]:
        return {
            "hard_mode": True,
            "readiness": self.readiness(),
            "escalation_ladder": self.fallback.ladder(),
            "content_simulator": self.simulator.generate_config(),
            "llm_defender": self.llm_defender.generate_config(),
            "mesh_p2p": self.mesh.generate_config(),
            "personal_servers": self.personal_servers.generate_config(),
        }
