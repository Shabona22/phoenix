"""Kill switch – iptables/pf rules with dry-run support."""

from __future__ import annotations

import platform
import subprocess
from typing import List


class KillSwitch:
    def __init__(self, vpn_interface: str = "tun0", dry_run: bool = True):
        self.vpn_interface = vpn_interface
        self.dry_run = dry_run
        self._active = False

    @property
    def is_active(self) -> bool:
        return self._active

    def _build_iptables_rules(self) -> List[str]:
        return [
            "iptables -P OUTPUT DROP",
            f"iptables -A OUTPUT -o {self.vpn_interface} -j ACCEPT",
            "iptables -A OUTPUT -o lo -j ACCEPT",
            "iptables -A OUTPUT -d 127.0.0.0/8 -j ACCEPT",
        ]

    def _build_pf_rules(self) -> List[str]:
        return [
            f"block out all",
            f"pass out on {self.vpn_interface} all",
            "pass out on lo0 all",
        ]

    def get_rules(self) -> List[str]:
        system = platform.system()
        if system == "Darwin":
            return self._build_pf_rules()
        return self._build_iptables_rules()

    def enable(self) -> bool:
        rules = self.get_rules()
        if self.dry_run:
            self._active = True
            return True

        system = platform.system()
        try:
            if system == "Darwin":
                rule_text = "\n".join(rules)
                subprocess.run(["pfctl", "-e"], check=False, capture_output=True)
                subprocess.run(["pfctl", "-f", "-"], input=rule_text.encode(), check=True)
            else:
                for rule in rules:
                    subprocess.run(rule.split(), check=True)
            self._active = True
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def disable(self) -> bool:
        if self.dry_run:
            self._active = False
            return True
        try:
            subprocess.run(["iptables", "-P", "OUTPUT", "ACCEPT"], check=False)
            subprocess.run(["iptables", "-F"], check=False)
            self._active = False
            return True
        except FileNotFoundError:
            return False
