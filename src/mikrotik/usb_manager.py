#!/usr/bin/env python3
"""USB flash management for MikroTik hap ax3 offline deploy."""

from __future__ import annotations

from pathlib import Path
from typing import Callable, List, Optional


DEFAULT_USB_MOUNTS = ("/usb1", "/usb1/phoenix", "/disk1/phoenix")


class UsbManager:
    def __init__(self, probe_fn: Optional[Callable[[], List[str]]] = None) -> None:
        self._probe_fn = probe_fn

    def list_usb_mounts(self) -> List[str]:
        if self._probe_fn:
            return self._probe_fn()
        return list(DEFAULT_USB_MOUNTS)

    def export_scripts_to_usb(
        self,
        scripts_dir: str | Path,
        usb_mount: str = "/usb1/phoenix",
    ) -> str:
        scripts_path = Path(scripts_dir)
        lines = [
            f"# Phoenix USB export to {usb_mount}",
            f":do {{ /file mkdir {usb_mount} }} on-error={{}}",
        ]
        for script_file in sorted(scripts_path.glob("*.rsc")):
            dest = f"{usb_mount}/{script_file.name}"
            lines.append(
                f':do {{ /file copy source=/{script_file.name} destination={dest} }} on-error={{}}'
            )
            lines.append(f':log info "phoenix: copied {script_file.name} to USB"')
        lines.append(':log info "phoenix: usb export complete"')
        return "\n".join(lines) + "\n"

    def generate_usb_backup_script(self, usb_mount: str = "/usb1/phoenix") -> str:
        backup_name = f"{usb_mount}/phoenix-backup"
        return f"""
# Phoenix USB backup
:do {{ /file mkdir {usb_mount} }} on-error={{}}
/system backup save name=phoenix-backup
:do {{ /file copy source=/phoenix-backup.backup destination={backup_name}.backup }} on-error={{}}
/export file={usb_mount}/phoenix-config
:log info "phoenix: usb backup saved"
"""
