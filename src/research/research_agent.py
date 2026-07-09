"""Research Agent – collect and analyze DBF-related censorship intelligence."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Dict, List

try:
    import requests
except ImportError:  # pragma: no cover
    requests = None  # type: ignore[assignment]


class ResearchAgent:
    """Gather external signals and produce protocol recommendations."""

    DEFAULT_SOURCES = {
        "netblocks": "https://api.netblocks.org/reports/iran",
        "dbf_reports": "https://filtershekan.sbs/DBF/",
    }

    def __init__(self, sources: Dict[str, str] | None = None, timeout: int = 5) -> None:
        self.sources = sources or dict(self.DEFAULT_SOURCES)
        self.timeout = timeout
        self.findings: List[Dict[str, Any]] = []

    def collect_data(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "sources": [],
            "key_findings": [],
        }

        for name, url in self.sources.items():
            payload = self._fetch_source(name, url)
            if payload:
                data["sources"].append(payload)

        data["key_findings"] = self._extract_findings(data["sources"])
        self.findings = data["key_findings"]
        return data

    def _fetch_source(self, name: str, url: str) -> Dict[str, Any] | None:
        if requests is None:
            return self._offline_source(name)

        try:
            response = requests.get(url, timeout=self.timeout)
            if response.status_code != 200:
                return self._offline_source(name)
            content: Any
            try:
                content = response.json()
            except ValueError:
                content = response.text[:500]
            return {"name": name, "url": url, "data": content}
        except (OSError, requests.RequestException):
            return self._offline_source(name)

    def _offline_source(self, name: str) -> Dict[str, Any]:
        """Deterministic fallback when live sources are unavailable."""
        if name == "dbf_reports":
            return {
                "name": name,
                "url": "offline",
                "data": "Degradation-Based Filtering and TLS fingerprint blocking observed.",
            }
        return {
            "name": name,
            "url": "offline",
            "data": {"connectivity": 45, "note": "offline estimate"},
        }

    def _extract_findings(self, sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        findings: List[Dict[str, Any]] = []
        for source in sources:
            name = source.get("name", "")
            data = source.get("data", {})

            if name == "netblocks" and isinstance(data, dict) and "connectivity" in data:
                findings.append(
                    {
                        "type": "connectivity",
                        "value": data["connectivity"],
                        "description": "Iran internet connectivity index",
                    }
                )
            if name == "dbf_reports":
                text = data if isinstance(data, str) else json.dumps(data)
                if "Degradation" in text or "Fingerprint" in text:
                    findings.append(
                        {
                            "type": "dbf_detected",
                            "value": True,
                            "description": "Degradation-Based Filtering indicators present",
                        }
                    )
        return findings

    def analyze_findings(self, data: Dict[str, Any] | None = None) -> Dict[str, Any]:
        payload = data or {"key_findings": self.findings}
        findings = payload.get("key_findings", [])
        recommendations: List[Dict[str, str]] = []

        for finding in findings:
            if finding.get("type") == "connectivity" and float(finding.get("value", 100)) < 50:
                recommendations.append(
                    {
                        "protocol": "websocket_plain",
                        "reason": "Low connectivity – prefer no-TLS transports",
                    }
                )
            if finding.get("type") == "dbf_detected":
                recommendations.append(
                    {
                        "protocol": "no_tls",
                        "reason": "DBF detected – deprioritize TLS fingerprinted protocols",
                    }
                )

        if not recommendations:
            recommendations.append(
                {"protocol": "websocket_plain", "reason": "Default DBF-safe baseline"}
            )

        return {
            "findings": findings,
            "recommendations": recommendations,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def generate_report(self) -> str:
        data = self.collect_data()
        analysis = self.analyze_findings(data)
        return (
            "# Research Agent Report\n\n"
            f"Generated: {analysis['timestamp']}\n\n"
            "## Key Findings\n"
            f"{json.dumps(data['key_findings'], indent=2)}\n\n"
            "## Recommendations\n"
            f"{json.dumps(analysis['recommendations'], indent=2)}\n"
        )
