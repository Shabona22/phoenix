"""Registry of user-owned personal servers used as last-resort fallbacks.

These are servers the user controls outside the Doprax fleet (a friend's VPS, a
home box, etc.). They can be reached over SSH and are the final tier when the
managed nodes are all blocked.
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class PersonalServer:
    name: str
    ip: str
    ssh_port: int = 22
    username: str = "root"
    auth: str = "password"  # "password" | "key"
    protocols: List[str] = field(default_factory=lambda: ["ssh_tunnel"])
    trusted: bool = True
    location: str = "unknown"
    fixed_ip: bool = True


class PersonalServerManager:
    def __init__(self, store_path: Optional[str] = None):
        base = Path(os.getenv("PHOENIX_OUTPUT_DIR", "phoenix-output"))
        self.store_path = Path(store_path) if store_path else base / "personal_servers.json"
        self.servers: Dict[str, PersonalServer] = {}

    def add(self, server: PersonalServer) -> None:
        self.servers[server.name] = server

    def remove(self, name: str) -> bool:
        return self.servers.pop(name, None) is not None

    def list(self) -> List[PersonalServer]:
        return list(self.servers.values())

    def best(self) -> Optional[PersonalServer]:
        trusted = [s for s in self.servers.values() if s.trusted]
        pool = trusted or list(self.servers.values())
        return pool[0] if pool else None

    def save(self) -> Path:
        self.store_path.parent.mkdir(parents=True, exist_ok=True)
        data = {name: asdict(srv) for name, srv in self.servers.items()}
        self.store_path.write_text(json.dumps(data, indent=2))
        return self.store_path

    def load(self) -> None:
        if not self.store_path.exists():
            return
        try:
            data = json.loads(self.store_path.read_text())
        except (ValueError, OSError):
            return
        for name, raw in data.items():
            self.servers[name] = PersonalServer(**raw)

    def generate_config(self) -> Dict[str, object]:
        return {
            "enabled": bool(self.servers),
            "count": len(self.servers),
            "servers": [asdict(s) for s in self.servers.values()],
        }
