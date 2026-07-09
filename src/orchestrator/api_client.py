"""Doprax API client for VM lifecycle management."""

from __future__ import annotations

import os
import uuid
from typing import Any, Dict, List, Optional

import requests
from dotenv import load_dotenv

load_dotenv()


class DopraxAPIError(Exception):
    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code


class DopraxClient:
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: int = 30,
    ):
        self.api_key = api_key or os.getenv("DOPRAX_API_KEY", "")
        self.base_url = (base_url or os.getenv("DOPRAX_BASE_URL", "https://www.doprax.com")).rstrip("/")
        self.timeout = timeout
        if not self.api_key:
            raise DopraxAPIError("DOPRAX_API_KEY is not set")

    def _headers(self) -> Dict[str, str]:
        return {
            "X-API-Key": self.api_key,
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "phoenix-vpn/10.0",
        }

    def _request(self, method: str, path: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        url = f"{self.base_url}{path}"
        response = requests.request(
            method,
            url,
            headers=self._headers(),
            json=data,
            timeout=self.timeout,
        )
        try:
            payload = response.json() if response.content else {}
        except ValueError:
            payload = {"raw": response.text}

        if response.status_code >= 400:
            err = payload.get("error") or {}
            msg = err.get("message") or payload.get("msg") or payload.get("message") or response.text
            raise DopraxAPIError(str(msg), response.status_code)

        return payload

    def list_vms(self) -> List[Dict[str, Any]]:
        result = self._request("GET", "/api/v1/vms/")
        return result.get("data", result if isinstance(result, list) else [])

    def get_vm(self, vm_code: str) -> Dict[str, Any]:
        result = self._request("GET", f"/api/v1/vms/{vm_code}/")
        return result.get("data", result)

    def create_vm(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        if payload.get("product_version_id"):
            return self.create_vm_v2(payload)
        result = self._request("POST", "/api/v1/vms/", data=payload)
        return result.get("data", result)

    def get_catalogue(self, provider: Optional[str] = None) -> List[Dict[str, Any]]:
        params = f"?provider={provider}" if provider else ""
        result = self._request("GET", f"/api/v2/catalogue/service-catalogue/{params}")
        return result.get("data", [])

    def create_vm_v2(
        self,
        payload: Dict[str, Any],
        *,
        product_version_id: Optional[str] = None,
        name: Optional[str] = None,
        location_code: Optional[str] = None,
        os_code: str = "ubuntu_22_04",
    ) -> Dict[str, Any]:
        body = dict(payload)
        if product_version_id:
            body["product_version_id"] = product_version_id
        if name:
            body["name"] = name
        if location_code:
            body.setdefault("selections", {})
            body["selections"]["location"] = {"code": location_code}
            body["selections"].setdefault("operating_system", {"code": os_code})
        body.setdefault("idempotency_key", str(uuid.uuid4()))
        result = self._request("POST", "/api/v2/services/instances/", data=body)
        return result.get("data", result)

    def delete_vm(self, vm_code: str) -> Dict[str, Any]:
        return self._request("DELETE", f"/api/v1/vms/{vm_code}/")

    def rebuild_vm(self, vm_code: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return self._request("POST", f"/api/v1/vms/{vm_code}/rebuild/", data=payload or {})

    def send_command(self, vm_code: str, command: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        body = {"command": command, **(params or {})}
        return self._request("POST", f"/api/v1/vms/{vm_code}/commands/", data=body)

    def start_vm(self, vm_code: str) -> Dict[str, Any]:
        return self.send_command(vm_code, "start")

    def stop_vm(self, vm_code: str) -> Dict[str, Any]:
        return self.send_command(vm_code, "stop")

    def restart_vm(self, vm_code: str) -> Dict[str, Any]:
        return self.send_command(vm_code, "restart")

    def get_status(self, vm_code: str) -> Dict[str, Any]:
        result = self._request("GET", f"/api/v1/vms/{vm_code}/status/")
        return result.get("data", result)

    def get_ips(self, vm_code: str) -> List[Dict[str, Any]]:
        result = self._request("GET", f"/api/v1/vms/{vm_code}/ips/")
        data = result.get("data", result)
        return data if isinstance(data, list) else [data]

    def get_traffic(self, vm_code: str) -> Dict[str, Any]:
        result = self._request("GET", f"/api/v1/vms/{vm_code}/traffic/")
        return result.get("data", result)

    def get_password(self, vm_code: str) -> Dict[str, Any]:
        result = self._request("GET", f"/api/v1/vms/{vm_code}/password/")
        return result.get("data", result)

    def get_vm_access(self, vm_code: str) -> Dict[str, Any]:
        result = self._request("GET", f"/api/v2/vms/{vm_code}/actions/access/")
        return result.get("data", result)

    def list_providers(self) -> List[Dict[str, Any]]:
        result = self._request("GET", "/api/v1/vproviders/")
        return result.get("data", result if isinstance(result, list) else [])

    def list_provider_locations(self, provider_code: str) -> List[Dict[str, Any]]:
        result = self._request("GET", f"/api/v1/vproviders/{provider_code}/locations/")
        return result.get("data", result if isinstance(result, list) else [])
