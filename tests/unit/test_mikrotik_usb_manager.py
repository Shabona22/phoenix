"""Unit tests for UsbManager."""

from __future__ import annotations

from pathlib import Path

from mikrotik.usb_manager import UsbManager, DEFAULT_USB_MOUNTS


def test_list_usb_mounts_default():
    mgr = UsbManager()
    mounts = mgr.list_usb_mounts()
    assert "/usb1/phoenix" in mounts
    assert mounts == list(DEFAULT_USB_MOUNTS)


def test_list_usb_mounts_custom_probe():
    mgr = UsbManager(probe_fn=lambda: ["/custom/usb"])
    assert mgr.list_usb_mounts() == ["/custom/usb"]


def test_export_scripts_to_usb(tmp_path):
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    (scripts / "dns_cache.rsc").write_text("# test")
    (scripts / "monitoring.rsc").write_text("# test")

    output = UsbManager().export_scripts_to_usb(scripts, usb_mount="/usb1/phoenix")
    assert "/usb1/phoenix" in output
    assert "dns_cache.rsc" in output
    assert "monitoring.rsc" in output
    assert "file copy" in output


def test_generate_usb_backup_script():
    script = UsbManager().generate_usb_backup_script("/usb1/phoenix")
    assert "/system backup save" in script
    assert "/export file=" in script
    assert "phoenix-backup" in script


def test_export_empty_dir(tmp_path):
    scripts = tmp_path / "empty"
    scripts.mkdir()
    output = UsbManager().export_scripts_to_usb(scripts)
    assert "usb export complete" in output
