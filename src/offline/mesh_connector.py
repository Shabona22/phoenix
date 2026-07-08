"""Bluetooth/mesh connector scaffold."""

from __future__ import annotations

import json
import platform
from typing import Dict, Optional


class MeshConnector:
    """OS-level Bluetooth mesh is not available in headless Python; this provides a config scaffold."""

    def __init__(self, device_name: str = "phoenix-mesh"):
        self.device_name = device_name
        self._connected = False

    @property
    def platform(self) -> str:
        return platform.system()

    def generate_config(self, payload: Optional[Dict[str, object]] = None) -> Dict[str, object]:
        return {
            "enabled": False,
            "device_name": self.device_name,
            "platform": self.platform,
            "note": "Bluetooth mesh requires native OS APIs; enable manually on supported devices.",
            "payload_size_limit": 512,
            "payload_preview": json.dumps(payload or {})[:128],
        }

    def connect(self) -> bool:
        self._connected = False
        return False

    def disconnect(self) -> None:
        self._connected = False
