"""Unit tests for obfuscation modules."""

from obfuscation.behavioral_morphing import BehavioralMorphing
from obfuscation.fake_ip_resolver import FakeIPResolver
from obfuscation.fragmenter import Fragmenter
from obfuscation.jitter import Jitter
from obfuscation.noise_generator import NoiseGenerator
from obfuscation.padding import Padding
from obfuscation.port_rotator import PortRotator
from obfuscation.sni_rotator import SNIRotator
from obfuscation.udp2raw_wrapper import Udp2RawWrapper


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


def test_udp2raw_wrapper():
    wrapper = Udp2RawWrapper()
    cfg = wrapper.generate_config("93.114.98.9")
    assert cfg["enabled"] is True
    assert "udp2raw" in cfg["command"]


def test_fragmenter_roundtrip():
    frag = Fragmenter(chunk_size=8)
    payload = b"phoenix-vpn-test-payload"
    chunks = frag.fragment(payload)
    assert frag.reassemble(chunks) == payload


def test_noise_generator():
    gen = NoiseGenerator(16, 32)
    packets = gen.generate(3)
    assert len(packets) == 3
    assert all(16 <= len(p) <= 32 for p in packets)


def test_fake_ip_resolver():
    resolver = FakeIPResolver()
    ip = resolver.resolve("example.com")
    assert ip in resolver.DECOY_IPS
    cfg = resolver.generate_config()
    assert cfg["enabled"] is True
