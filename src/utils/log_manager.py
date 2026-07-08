"""Centralized log manager."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Optional


class LogManager:
    def __init__(self, name: str = "phoenix", log_dir: Optional[str] = None):
        self.log_dir = Path(log_dir or os.getenv("PHOENIX_OUTPUT_DIR", "phoenix-output")) / "logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(name)
        if not self.logger.handlers:
            self._setup()

    def _setup(self) -> None:
        self.logger.setLevel(logging.INFO)
        fh = logging.FileHandler(self.log_dir / "phoenix.log")
        fh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
        ch = logging.StreamHandler()
        ch.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
        self.logger.addHandler(fh)
        self.logger.addHandler(ch)

    def info(self, msg: str) -> None:
        self.logger.info(msg)

    def warning(self, msg: str) -> None:
        self.logger.warning(msg)

    def error(self, msg: str) -> None:
        self.logger.error(msg)
