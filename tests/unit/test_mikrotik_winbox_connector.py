"""Unit tests for WinBoxConnector with mock transport."""

from __future__ import annotations

import struct
from typing import List

import pytest

from mikrotik.winbox_connector import WinBoxConnector


class MockTransport:
    def __init__(self, responses: List[bytes] | None = None) -> None:
        self.sent: List[bytes] = []
        self._buffer = b"".join(responses or [])
        self.connected = False

    def connect(self, host: str, port: int) -> None:
        self.connected = True

    def close(self) -> None:
        self.connected = False

    def send(self, data: bytes) -> None:
        self.sent.append(data)

    def recv(self, size: int) -> bytes:
        chunk = self._buffer[:size]
        self._buffer = self._buffer[size:]
        return chunk


def _sentence(words: List[str]) -> bytes:
    payload = b""
    for word in words:
        encoded = word.encode()
        payload += struct.pack(">I", len(encoded)) + encoded
    payload += struct.pack(">I", 0)
    return payload


def test_connect_success_with_plain_login():
    transport = MockTransport([_sentence(["!done"])])
    client = WinBoxConnector("192.168.88.1", "admin", "pass", transport=transport)
    assert client.connect() is True
    client.close()


def test_connect_failure_on_os_error():
    class FailingTransport(MockTransport):
        def connect(self, host: str, port: int) -> None:
            raise OSError("refused")

    client = WinBoxConnector("192.168.88.1", "admin", "pass", transport=FailingTransport())
    assert client.connect() is False


def test_send_command_requires_connection():
    transport = MockTransport()
    client = WinBoxConnector("192.168.88.1", "admin", "pass", transport=transport)
    with pytest.raises(RuntimeError, match="not connected"):
        client.send_command("/system resource print")


def test_send_command_parses_reply():
    transport = MockTransport([_sentence(["!re", "=name=admin"]), _sentence(["!done"])])
    client = WinBoxConnector("192.168.88.1", "admin", "pass", transport=transport)
    client._connected = True
    results = client.send_command("/user print")
    assert results == [{"name": "admin"}]


def test_upload_script_sends_add_command():
    responses = [
        _sentence(["!done"]),
        _sentence(["!done"]),
        _sentence(["!done"]),
    ]
    transport = MockTransport(responses)
    client = WinBoxConnector("192.168.88.1", "admin", "pass", transport=transport)
    client._connected = True
    ok = client.upload_script("dns_cache", ":log info test")
    assert ok is True
    assert len(transport.sent) >= 2


def test_run_script_returns_string():
    transport = MockTransport([_sentence(["!done"])])
    client = WinBoxConnector("192.168.88.1", "admin", "pass", transport=transport)
    client._connected = True
    result = client.run_script("dns_cache")
    assert "[]" in result or result == "[]"


def test_import_rsc_delegates_to_upload_and_run():
    transport = MockTransport(
        [
            _sentence(["!done"]),
            _sentence(["!done"]),
            _sentence(["!done"]),
            _sentence(["!done"]),
        ]
    )
    client = WinBoxConnector("192.168.88.1", "admin", "pass", transport=transport)
    client._connected = True
    assert client.import_rsc(":log info import", name="phoenix-import") is True


def test_default_port_is_8728():
    client = WinBoxConnector("1.1.1.1", "u", "p")
    assert client.port == 8728
