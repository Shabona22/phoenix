"""Unit tests for security modules."""

from security.dns_leak_check import DNSLeakCheck
from security.kill_switch import KillSwitch
from security.tls_fingerprint import TLSFingerprint
from security.webrtc_leak_check import WebRTCLeakCheck


def test_kill_switch_dry_run():
    ks = KillSwitch(dry_run=True)
    assert ks.enable() is True
    assert ks.is_active is True
    rules = ks.get_rules()
    assert len(rules) > 0
    assert ks.disable() is True


def test_tls_fingerprint_rotate():
    fp = TLSFingerprint()
    first = fp.current_profile()["name"]
    fp.rotate()
    second = fp.current_profile()["name"]
    assert first != second or len(fp.PROFILES) == 1


def test_dns_leak_check_structure():
    checker = DNSLeakCheck()
    result = checker.check_resolver()
    assert "leaked" in result
    assert "resolvers" in result


def test_webrtc_leak_private_ip():
    checker = WebRTCLeakCheck()
    result = checker.check(["192.168.1.5"])
    assert result["leaked"] is True
