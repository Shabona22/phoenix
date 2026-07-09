"""Collect Iran network status from multiple sources."""

from __future__ import annotations

import shutil
import subprocess
import time
from typing import Any, Callable, Dict, List, Optional

try:
    import requests
except ImportError:  # pragma: no cover
    requests = None  # type: ignore[assignment]

from monitoring.user_report_collector import UserReportCollector
from research.research_agent import ResearchAgent

ProbeFn = Callable[[str, str], Dict[str, Any]]


class DataCollector:
    DEFAULT_TEST_IPS = ["1.1.1.1", "8.8.8.8", "208.67.222.222"]
    DEFAULT_TEST_DOMAINS = ["google.com", "github.com", "cloudflare.com"]

    def __init__(
        self,
        research_agent: Optional[ResearchAgent] = None,
        user_collector: Optional[UserReportCollector] = None,
        probe_fn: Optional[ProbeFn] = None,
        timeout: int = 5,
    ) -> None:
        self.research = research_agent or ResearchAgent(sources={})
        self.user_collector = user_collector or UserReportCollector()
        self.probe_fn = probe_fn
        self.timeout = timeout
        self.test_ips = list(self.DEFAULT_TEST_IPS)
        self.test_domains = list(self.DEFAULT_TEST_DOMAINS)

    def collect_all(self) -> Dict[str, Any]:
        return {
            "timestamp": time.time(),
            "netblocks": self._fetch_netblocks(),
            "ping_tests": self._run_ping_tests(),
            "dns_tests": self._run_dns_tests(),
            "http_tests": self._run_http_tests(),
            "user_reports": self.user_collector.get_stats(),
        }

    def _fetch_netblocks(self) -> Dict[str, Any]:
        data = self.research.collect_data()
        for source in data.get("sources", []):
            if source.get("name") == "netblocks":
                return {"status": "ok", "data": source.get("data", {})}
        return {"status": "unavailable", "data": {}}

    def _run_ping_tests(self) -> Dict[str, Any]:
        results: Dict[str, Any] = {}
        for ip in self.test_ips:
            results[ip] = self._probe("ping", ip)
        return results

    def _run_dns_tests(self) -> Dict[str, Any]:
        results: Dict[str, Any] = {}
        for domain in self.test_domains:
            results[domain] = self._probe("dns", domain)
        return results

    def _run_http_tests(self) -> Dict[str, Any]:
        results: Dict[str, Any] = {}
        for domain in self.test_domains:
            results[domain] = self._probe("http", domain)
        return results

    def _probe(self, kind: str, target: str) -> Dict[str, Any]:
        if self.probe_fn:
            return self.probe_fn(kind, target)
        if kind == "ping":
            return self._ping(target)
        if kind == "dns":
            return self._dns(target)
        return self._http(target)

    def _ping(self, ip: str) -> Dict[str, Any]:
        if not shutil.which("ping"):
            return {"success": False, "error": "ping unavailable"}
        try:
            result = subprocess.run(
                ["ping", "-c", "3", "-W", "2", ip],
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )
            return {"success": result.returncode == 0, "output": result.stdout[:200]}
        except (OSError, subprocess.TimeoutExpired):
            return {"success": False, "error": "timeout"}

    def _dns(self, domain: str) -> Dict[str, Any]:
        if not shutil.which("dig"):
            return {"success": False, "error": "dig unavailable"}
        try:
            result = subprocess.run(
                ["dig", domain, "@1.1.1.1", "+short"],
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )
            ip = result.stdout.strip()
            return {"success": bool(ip), "ip": ip}
        except (OSError, subprocess.TimeoutExpired):
            return {"success": False, "error": "timeout"}

    def _http(self, domain: str) -> Dict[str, Any]:
        if requests is None:
            return {"success": False, "error": "requests unavailable"}
        try:
            response = requests.get(f"https://{domain}", timeout=self.timeout)
            return {
                "success": response.status_code == 200,
                "status_code": response.status_code,
                "latency": int(response.elapsed.total_seconds() * 1000),
            }
        except (OSError, requests.RequestException):
            return {"success": False, "error": "timeout"}
