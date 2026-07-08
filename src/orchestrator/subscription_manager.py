"""Subscription export manager."""

from __future__ import annotations

import base64
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import quote


class SubscriptionManager:
    def __init__(self, output_dir: Optional[str] = None):
        self.output_dir = Path(output_dir or os.getenv("PHOENIX_OUTPUT_DIR", "phoenix-output")) / "subscriptions"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _build_uri(self, protocol: str, config: Dict[str, Any]) -> str:
        server = config.get("server", {})
        ip = server.get("ip", "")
        port = server.get("port", 0)

        if protocol == "shadowsocks":
            method = config.get("cipher", "aes-256-gcm")
            password = config.get("password", "")
            return f"ss://{base64.urlsafe_b64encode(f'{method}:{password}@{ip}:{port}'.encode()).decode().rstrip('=')}"

        if protocol == "xray":
            uuid = config.get("uuid", "")
            return f"vless://{uuid}@{ip}:{port}?security=reality&type=tcp"

        if protocol == "wireguard":
            return f"wireguard://{ip}:{port}"

        if protocol == "hysteria":
            password = config.get("auth", {}).get("password", "")
            return f"hysteria://{ip}:{port}?auth={quote(password)}"

        return f"{protocol}://{ip}:{port}"

    def export_json(self, node_id: str, configs: Dict[str, Any]) -> Path:
        dest = self.output_dir / f"{node_id}.json"
        dest.write_text(json.dumps(configs, indent=2))
        return dest

    def export_base64_uri_list(self, node_id: str, configs: Dict[str, Any]) -> Path:
        uris: List[str] = []
        for proto, data in configs.items():
            cfg = data.get("config", data) if isinstance(data, dict) else data
            uris.append(self._build_uri(proto, cfg))

        encoded = base64.b64encode("\n".join(uris).encode()).decode()
        dest = self.output_dir / f"{node_id}.txt"
        dest.write_text(encoded)
        return dest

    def export_all(self, all_configs: Dict[str, Dict[str, Any]]) -> List[Path]:
        paths: List[Path] = []
        for node_id, configs in all_configs.items():
            paths.append(self.export_json(node_id, configs))
            paths.append(self.export_base64_uri_list(node_id, configs))
        return paths
