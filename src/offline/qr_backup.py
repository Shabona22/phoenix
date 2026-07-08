"""QR code backup for offline config sharing."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict, Optional

import qrcode


class QRBackup:
    def __init__(self, output_dir: Optional[str] = None):
        self.output_dir = Path(output_dir or os.getenv("PHOENIX_OUTPUT_DIR", "phoenix-output")) / "qr"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate(self, config: Dict[str, object], name: str = "backup") -> Path:
        data = json.dumps(config, separators=(",", ":"))
        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        dest = self.output_dir / f"{name}.png"
        img.save(dest)
        return dest
