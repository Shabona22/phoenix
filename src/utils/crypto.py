"""Shared cryptographic utilities."""

import secrets
import string
from typing import Optional

from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey
from cryptography.hazmat.primitives import serialization


def generate_password(length: int = 16) -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def generate_random_port(low: int = 8000, high: int = 65000) -> int:
    return secrets.randbelow(high - low + 1) + low


def generate_token_hex(nbytes: int = 16) -> str:
    return secrets.token_hex(nbytes)


def generate_wireguard_keypair() -> tuple[str, str]:
    private_key = X25519PrivateKey.generate()
    private_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption(),
    )
    public_bytes = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    import base64

    priv = base64.b64encode(private_bytes).decode()
    pub = base64.b64encode(public_bytes).decode()
    return priv, pub


def generate_x25519_reality_keypair() -> tuple[str, str]:
    """Return (private_key, public_key) as base64url strings for Xray Reality."""
    private_key = X25519PrivateKey.generate()
    private_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption(),
    )
    public_bytes = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    import base64

    priv = base64.urlsafe_b64encode(private_bytes).decode().rstrip("=")
    pub = base64.urlsafe_b64encode(public_bytes).decode().rstrip("=")
    return priv, pub


def generate_uuid() -> str:
    import uuid

    return str(uuid.uuid4())
