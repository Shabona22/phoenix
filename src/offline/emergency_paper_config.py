"""Generate printable emergency config cards (QR + text) for offline users."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict, List, Optional

import qrcode
from PIL import Image, ImageDraw


class EmergencyPaperConfig:
    def __init__(self, output_dir: Optional[str] = None):
        base = Path(output_dir or os.getenv("PHOENIX_OUTPUT_DIR", "phoenix-output"))
        self.output_dir = base / "paper_configs"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_config_card(self, user_id: str, configs: List[Dict[str, object]]) -> Path:
        filename = self.output_dir / f"config_card_{user_id}.png"
        main_config = configs[0] if configs else {}

        img = Image.new("RGB", (800, 400), color="white")
        draw = ImageDraw.Draw(img)

        qr = qrcode.QRCode(box_size=5, border=2)
        qr.add_data(json.dumps(main_config, separators=(",", ":")))
        qr.make(fit=True)
        qr_pil = qr.make_image(fill_color="black", back_color="white")
        if hasattr(qr_pil, "get_image"):
            qr_pil = qr_pil.get_image()
        img.paste(qr_pil, (50, 50))

        server = main_config.get("server", {}) if isinstance(main_config.get("server"), dict) else {}
        draw.text((300, 50), f"User: {user_id}", fill="black")
        draw.text((300, 100), f"Protocol: {main_config.get('protocol', 'unknown')}", fill="black")
        draw.text((300, 150), f"Server: {server.get('ip', 'unknown')}", fill="black")
        draw.text((300, 200), f"Port: {server.get('port', 'unknown')}", fill="black")

        img.save(filename)
        return filename

    def generate_text_config(self, config: Dict[str, object]) -> str:
        user_id = str(config.get("user_id", "unknown"))
        server = config.get("server", {}) if isinstance(config.get("server"), dict) else {}
        lines = [
            "=" * 50,
            "PHOENIX VPN - EMERGENCY CONFIG",
            "=" * 50,
            "",
            f"User: {user_id}",
            f"Protocol: {config.get('protocol', 'unknown')}",
            f"Server: {server.get('ip', 'unknown')}",
            f"Port: {server.get('port', 'unknown')}",
            "",
            "Copy this config manually if QR doesn't work:",
            json.dumps(config, indent=2),
        ]
        text = "\n".join(lines)
        dest = self.output_dir / f"config_text_{user_id}.txt"
        dest.write_text(text)
        return text

    def generate_bundle(self, user_id: str, configs: List[Dict[str, object]]) -> Dict[str, str]:
        card = self.generate_config_card(user_id, configs)
        text = self.generate_text_config({**(configs[0] if configs else {}), "user_id": user_id})
        return {"card": str(card), "text_preview": text[:200]}
