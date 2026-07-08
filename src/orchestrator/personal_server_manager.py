"""Orchestrator-facing personal server registry (non-cloud, fixed IP)."""

from __future__ import annotations

import json
from typing import Dict, List

from hard_mode.personal_server_manager import PersonalServer, PersonalServerManager


class OrchestratorPersonalServerManager(PersonalServerManager):
    """Extends Hard Mode personal servers with orchestrator deploy hooks."""

    def add_server(
        self,
        name: str,
        ip: str,
        username: str = "root",
        password: str = "",
        location: str = "unknown",
        fixed_ip: bool = True,
        trusted: bool = True,
    ) -> bool:
        if name in self.servers:
            return False
        self.add(
            PersonalServer(
                name=name,
                ip=ip,
                username=username,
                auth="password" if password else "key",
                trusted=trusted,
                location=location,
                fixed_ip=fixed_ip,
            )
        )
        self.save()
        return True

    def get_active_servers(self) -> List[PersonalServer]:
        return [s for s in self.servers.values() if s.trusted]

    def deploy_to_personal_server(self, name: str, config: Dict[str, object]) -> bool:
        server = self.servers.get(name)
        if not server:
            return False
        bundle_path = self.store_path.parent / "personal_deploy" / f"{name}_config.json"
        bundle_path.parent.mkdir(parents=True, exist_ok=True)
        bundle_path.write_text(
            json.dumps({"server": server.name, "ip": server.ip, "config": config}, indent=2)
        )
        return bundle_path.exists()

    def generate_config(self) -> Dict[str, object]:
        base = super().generate_config()
        base["non_cloud"] = True
        base["fixed_ip_servers"] = sum(1 for s in self.servers.values() if getattr(s, "fixed_ip", False))
        return base
