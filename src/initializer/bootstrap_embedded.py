"""Self-contained bootstrap bundle generator."""

from __future__ import annotations

import json
import os
import zipfile
from pathlib import Path
from typing import Dict, Optional


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
                zf.writestr(f"configs/{proto}.json", json.dumps(data, indent=2))

        return bundle_path
