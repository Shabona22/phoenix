#!/usr/bin/env python3
"""RouterOS API client (port 8728) for MikroTik deployment.

Note: class is named WinBoxConnector per Phoenix spec; transport uses
RouterOS API binary protocol, not the WinBox GUI protocol on port 8291.
"""

from __future__ import annotations

import hashlib
import socket
import struct
from typing import Any, Dict, List, Optional, Protocol


class ApiTransport(Protocol):
    def connect(self, host: str, port: int) -> None: ...
    def close(self) -> None: ...
    def send(self, data: bytes) -> None: ...
    def recv(self, size: int) -> bytes: ...


class SocketTransport:
    def __init__(self) -> None:
        self._sock: Optional[socket.socket] = None

    def connect(self, host: str, port: int) -> None:
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.settimeout(30)
        self._sock.connect((host, port))

    def close(self) -> None:
        if self._sock:
            self._sock.close()
            self._sock = None

    def send(self, data: bytes) -> None:
        if not self._sock:
            raise RuntimeError("not connected")
        self._sock.sendall(data)

    def recv(self, size: int) -> bytes:
        if not self._sock:
            raise RuntimeError("not connected")
        return self._sock.recv(size)


class WinBoxConnector:
    def __init__(
        self,
        ip: str,
        username: str,
        password: str,
        port: int = 8728,
        transport: Optional[ApiTransport] = None,
    ) -> None:
        self.ip = ip
        self.username = username
        self.password = password
        self.port = port
        self.transport = transport or SocketTransport()
        self._connected = False

    def connect(self) -> bool:
        try:
            self.transport.connect(self.ip, self.port)
            self._write_sentence(["/login", f"=name={self.username}", f"=password={self.password}"])
            reply = self._read_sentence()
            if reply and reply[0] == "!done":
                self._connected = True
                return True
            if reply and reply[0] == "!trap":
                challenge = self._extract_challenge(reply)
                if challenge:
                    return self._login_with_challenge(challenge)
            return False
        except OSError:
            return False

    def _extract_challenge(self, reply: List[str]) -> Optional[bytes]:
        for word in reply:
            if word.startswith("=ret="):
                return bytes.fromhex(word[5:])
        return None

    def _login_with_challenge(self, challenge: bytes) -> bool:
        md = hashlib.md5()
        md.update(b"\x00")
        md.update(self.password.encode())
        md.update(challenge)
        response = "00" + md.hexdigest()
        self._write_sentence(["/login", f"=name={self.username}", f"=response={response}"])
        reply = self._read_sentence()
        self._connected = bool(reply and reply[0] == "!done")
        return self._connected

    def send_command(self, command: str) -> List[Dict[str, Any]]:
        if not self._connected:
            raise RuntimeError("not connected")
        parts = [part for part in command.strip().split() if part]
        if not parts:
            return []
        self._write_sentence(parts)
        results: List[Dict[str, Any]] = []
        while True:
            sentence = self._read_sentence()
            if not sentence:
                break
            if sentence[0] == "!done":
                break
            if sentence[0] == "!re":
                results.append(self._sentence_to_dict(sentence[1:]))
            if sentence[0] == "!trap":
                results.append({"error": self._sentence_to_dict(sentence[1:])})
                break
        return results

    def upload_script(self, script_name: str, content: str) -> bool:
        escaped = content.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
        try:
            existing = self.send_command(f'/system script print where name="{script_name}"')
            if existing:
                self.send_command(f'/system script remove [find name="{script_name}"]')
            result = self.send_command(
                f'/system script add name="{script_name}" source="{escaped}"'
            )
            return not any("error" in item for item in result)
        except RuntimeError:
            return False

    def run_script(self, script_name: str) -> str:
        results = self.send_command(f"/system script run {script_name}")
        return str(results)

    def import_rsc(self, content: str, name: str = "phoenix-import") -> bool:
        return self.upload_script(name, content) and bool(self.run_script(name))

    def close(self) -> None:
        self.transport.close()
        self._connected = False

    def _write_sentence(self, words: List[str]) -> None:
        payload = b""
        for word in words:
            encoded = word.encode()
            payload += struct.pack(">I", len(encoded)) + encoded
        payload += struct.pack(">I", 0)
        self.transport.send(payload)

    def _read_sentence(self) -> List[str]:
        words: List[str] = []
        while True:
            length_bytes = self._recv_exact(4)
            if not length_bytes:
                return words
            length = struct.unpack(">I", length_bytes)[0]
            if length == 0:
                break
            words.append(self._recv_exact(length).decode())
        return words

    def _recv_exact(self, size: int) -> bytes:
        chunks: List[bytes] = []
        remaining = size
        while remaining > 0:
            chunk = self.transport.recv(remaining)
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        return b"".join(chunks)

    @staticmethod
    def _sentence_to_dict(words: List[str]) -> Dict[str, Any]:
        result: Dict[str, Any] = {}
        for word in words:
            if word.startswith("="):
                key, _, value = word[1:].partition("=")
                result[key] = value
        return result
