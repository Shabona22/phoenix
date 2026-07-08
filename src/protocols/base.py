"""Protocol base class for config generators."""

import secrets
import string
from abc import ABC, abstractmethod
from typing import Any, Dict


class ProtocolBase(ABC):
    def __init__(self, name: str, version: str):
        self.name = name
        self.version = version

    @abstractmethod
    def generate_config(self, server_ip: str, **kwargs) -> Dict[str, Any]:
        pass

    @abstractmethod
    def generate_client_config(self, config: Dict[str, Any]) -> str:
        pass

    def generate_server_config(self, config: Dict[str, Any]) -> str:
        raise NotImplementedError(f"{self.name} server config not implemented")

    def _generate_password(self, length: int = 16) -> str:
        alphabet = string.ascii_letters + string.digits
        return "".join(secrets.choice(alphabet) for _ in range(length))

    def _generate_random_port(self, low: int = 8000, high: int = 65000) -> int:
        return secrets.randbelow(high - low + 1) + low
