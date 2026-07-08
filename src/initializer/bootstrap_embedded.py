"""Self-contained bootstrap bundle generator."""

from __future__ import annotations

import json
import os
import zipfile
from pathlib import Path
from typing import Dict, Optional

from orchestrator.config_generator import ConfigGenerator


class BootstrapEmbedded:
    def __init__(self, output_dir: Optional[str] = None):
        self.output_dir = Path(output_dir or os.getenv("PHOENIX_OUTPUT_DIR", "phoenix-output")) / "bootstrap"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def create_bundle(self, configs: Dict[str, object], node_id: str) -> Path:
        bundle_path = self.output_dir / f"{node_id}_bootstrap.zip"
        manifest = {
            "version": "10.0",
            "node_id": node_id,
            "protocols": list(configs.keys()),
        }

        with zipfile.ZipFile(bundle_path, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("manifest.json", json.dumps(manifest, indent=2))
            for proto, data in configs.items():
                if not isinstance(data, dict):
                    continue
                cfg = data.get("config", data)
                zf.writestr(f"configs/{proto}/config.json", json.dumps(cfg, indent=2))
                if "client_config" in data:
                    ext = "conf" if proto in ("openvpn", "wireguard") else "txt"
                    zf.writestr(f"configs/{proto}/client.{ext}", data["client_config"])
                if "server_config" in data:
                    server_name, _ = ConfigGenerator.SERVER_FILES.get(proto, ("server.conf", "conf"))
                    zf.writestr(f"configs/{proto}/{server_name}", data["server_config"])

        return bundle_path
