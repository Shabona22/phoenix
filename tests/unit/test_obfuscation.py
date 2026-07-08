"""Unit tests for obfuscation modules."""

from obfuscation.behavioral_morphing import BehavioralMorphing
from obfuscation.jitter import Jitter
from obfuscation.padding import Padding
from obfuscation.port_rotator import PortRotator
from obfuscation.sni_rotator import SNIRotator


def test_sni_rotator():
    rot = SNIRotator(["a.com", "b.com"])
    assert rot.current() == "a.com"
    assert rot.rotate() == "b.com"


def test_padding_config():
    pad = Padding(32, 64)
    cfg = pad.generate_config()
    assert cfg["enabled"] is True
    assert len(pad.generate_padding()) >= 32


def test_jitter_range():
    j = Jitter(5, 10)
    delay = j.next_delay_ms()
    assert 5 <= delay <= 10


def test_port_rotator():
    rot = PortRotator([443, 8443])
    assert rot.current() == 443
    assert rot.rotate() == 8443


def test_behavioral_morphing():
    morph = BehavioralMorphing()
    cfg = morph.generate_config()
    assert cfg["enabled"] is True
    assert cfg["current_profile"] in morph.PROFILES
