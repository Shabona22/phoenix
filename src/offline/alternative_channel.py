"""Deliver configs through non-internet channels during prolonged outages."""

from __future__ import annotations

import base64
import json
import os
from pathlib import Path
from typing import Callable, Dict, List, Optional

from offline.mesh_connector import MeshP2P


class AlternativeChannel:
    """Try mesh, radio stub, SMS stub, then USB file export in order."""

    def __init__(self, output_dir: Optional[str] = None, mesh: Optional[MeshP2P] = None):
        base = Path(output_dir or os.getenv("PHOENIX_OUTPUT_DIR", "phoenix-output"))
        self.export_dir = base / "offline_exports"
        self.export_dir.mkdir(parents=True, exist_ok=True)
        self.mesh = mesh or MeshP2P()
        self.fallback_order = ["mesh", "radio", "sms", "usb"]
        self._handlers: Dict[str, Callable[[str, str], bool]] = {
            "mesh": self._send_mesh,
            "radio": self._send_radio,
            "sms": self._send_sms,
            "usb": self._send_usb,
        }
        self.last_channel: Optional[str] = None

    def encode_config(self, config: Dict[str, object]) -> str:
        return base64.b64encode(json.dumps(config, separators=(",", ":")).encode()).decode()

    def send_config(self, user_id: str, config: Dict[str, object]) -> bool:
        encoded = self.encode_config(config)
        for channel in self.fallback_order:
            if self._try_send(channel, user_id, encoded):
                self.last_channel = channel
                return True
        self.last_channel = None
        return False

    def _try_send(self, channel: str, user_id: str, payload: str) -> bool:
        handler = self._handlers.get(channel)
        if not handler:
            return False
        try:
            return handler(user_id, payload)
        except OSError:
            return False

    def _send_mesh(self, user_id: str, payload: str) -> bool:
        message = self.mesh.build_message("config", {"user_id": user_id, "payload": payload})
        reply = self.mesh.handle_message("local", message)
        return reply.get("type") == "ack"

    def _send_radio(self, user_id: str, payload: str) -> bool:
        # LoRa/RF requires hardware; record intent for manual broadcast.
        dest = self.export_dir / f"radio_{user_id}.txt"
        dest.write_text(payload)
        return dest.exists()

    def _send_sms(self, user_id: str, payload: str) -> bool:
        # SMS gateways need external API; store chunked payload for manual send.
        chunks = [payload[i : i + 120] for i in range(0, len(payload), 120)]
        dest = self.export_dir / f"sms_{user_id}.json"
        dest.write_text(json.dumps({"user_id": user_id, "chunks": chunks}, indent=2))
        return dest.exists()

    def _send_usb(self, user_id: str, payload: str) -> bool:
        dest = self.export_dir / f"config_{user_id}.txt"
        dest.write_text(payload)
        return dest.exists()

    def generate_config(self) -> Dict[str, object]:
        return {
            "enabled": True,
            "fallback_order": self.fallback_order,
            "export_dir": str(self.export_dir),
            "last_channel": self.last_channel,
        }
